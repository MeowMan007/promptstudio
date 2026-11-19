"""
TSK-042: Field run endpoint + streaming proposal.

A FieldRun orchestrates a single model invocation for one field on one artifact:
  1. Resolve the binding (TSK-040)
  2. Assemble the context bundle (TSK-041)
  3. Call the model (stubbed here; real impl plugs in model_adapter)
  4. Validate output against OutputContract
  5. Return a schema-valid PROPOSAL — never write directly
  6. Record cost (token counts)

Guarantees:
  - locked field → FieldRunError with code FIELD_LOCKED
  - cooldown active → FieldRunError with code COOLDOWN_ACTIVE
  - schema-invalid output → FieldRunError with code SCHEMA_VIOLATION
  - never applies a patch; always returns a proposal only
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any

from backend.app.bindings.assembler import (
    ArtifactContext,
    ContextBundle,
    assemble_context,
)
from backend.app.bindings.models import (
    AutoApplyPolicy,
    FieldBinding,
    resolve_binding,
)


# ---------------------------------------------------------------------------
# Request / Result types
# ---------------------------------------------------------------------------

@dataclass
class FieldRunRequest:
    """Everything needed to trigger a field run."""
    artifact_id: str
    artifact_type: str
    field_path: str          # e.g. "body" or "payload.acceptance_criteria"
    binding_id: str | None   # if None, resolved from binding registry
    run_id: str              # unique run identifier (caller-assigned)
    caller_role: str = "editor"
    # Optional context hints
    system_instructions: str | None = None
    jit_handles: dict[str, str] | None = None


@dataclass
class FieldRunResult:
    """Successful field run — contains a *proposal* only, never applied."""
    run_id: str
    binding_id: str
    artifact_id: str
    field_path: str
    proposal: dict[str, Any]       # {field_path: proposed_value}
    schema_valid: bool
    cost_tokens: int               # total tokens consumed (input + output)
    trace_id: str                  # unique trace for audit / DNA viewer
    bundle_hash: str               # hash of the context bundle used
    can_auto_apply: bool           # True only when policy.auto_apply allows


@dataclass
class FieldRunError:
    """Field run was rejected before or after model call."""
    run_id: str
    code: str           # FIELD_LOCKED | COOLDOWN_ACTIVE | BINDING_NOT_FOUND
                        # | SCHEMA_VIOLATION | CONTEXT_ERROR
    message: str
    detail: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Cooldown tracker (in-memory; real impl uses Redis / DB)
# ---------------------------------------------------------------------------

_last_run_at: dict[str, float] = {}   # key: f"{binding_id}:{artifact_id}"


def _cooldown_key(binding_id: str, artifact_id: str) -> str:
    return f"{binding_id}:{artifact_id}"


def _check_cooldown(binding: FieldBinding, artifact_id: str) -> float | None:
    """Return seconds remaining if still in cooldown, else None."""
    if binding.policy.cooldown_seconds <= 0:
        return None
    key = _cooldown_key(binding.id, artifact_id)
    last = _last_run_at.get(key)
    if last is None:
        return None
    elapsed = time.monotonic() - last
    remaining = binding.policy.cooldown_seconds - elapsed
    return remaining if remaining > 0 else None


def _record_run(binding: FieldBinding, artifact_id: str) -> None:
    if binding.policy.cooldown_seconds > 0:
        key = _cooldown_key(binding.id, artifact_id)
        _last_run_at[key] = time.monotonic()


# ---------------------------------------------------------------------------
# Schema validation against OutputContract
# ---------------------------------------------------------------------------

def _validate_against_contract(
    proposal_value: Any,
    binding: FieldBinding,
    field_path: str,
) -> list[str]:
    """
    Validate proposed value against OutputContract.
    Returns list of violation strings (empty = valid).
    """
    contract = binding.output_contract
    violations: list[str] = []

    # required_fields: only meaningful if proposal is a dict
    if isinstance(proposal_value, dict):
        for req in contract.required_fields:
            if req not in proposal_value:
                violations.append(f"required field missing: {req}")
        for forbidden in contract.forbidden_fields:
            if forbidden in proposal_value:
                violations.append(f"forbidden field present: {forbidden}")
        for arr_field, max_len in contract.max_array_length.items():
            if arr_field in proposal_value and isinstance(proposal_value[arr_field], list):
                if len(proposal_value[arr_field]) > max_len:
                    violations.append(
                        f"{arr_field} exceeds max_array_length {max_len} "
                        f"(got {len(proposal_value[arr_field])})"
                    )
    elif isinstance(proposal_value, list):
        # Top-level array field
        for arr_field, max_len in contract.max_array_length.items():
            if arr_field == field_path and len(proposal_value) > max_len:
                violations.append(
                    f"{field_path} exceeds max_array_length {max_len} "
                    f"(got {len(proposal_value)})"
                )

    # JSON schema validation (lightweight; full impl uses jsonschema lib)
    if contract.json_schema:
        schema_type = contract.json_schema.get("type")
        if schema_type == "string" and not isinstance(proposal_value, str):
            violations.append(f"expected string, got {type(proposal_value).__name__}")
        elif schema_type == "array" and not isinstance(proposal_value, list):
            violations.append(f"expected array, got {type(proposal_value).__name__}")
        elif schema_type == "object" and not isinstance(proposal_value, dict):
            violations.append(f"expected object, got {type(proposal_value).__name__}")
        min_len = contract.json_schema.get("minLength")
        if min_len is not None and isinstance(proposal_value, str) and len(proposal_value) < min_len:
            violations.append(f"string shorter than minLength {min_len}")

    return violations


# ---------------------------------------------------------------------------
# Model stub (real impl replaced by model_adapter in TSK-059)
# ---------------------------------------------------------------------------

def _stub_model_call(
    bundle: ContextBundle,
    field_path: str,
    *,
    artifact_type: str,
) -> tuple[Any, int]:
    """
    Stub model call — returns a deterministic synthetic proposal.
    Returns (proposed_value, output_tokens).
    Real impl will call model_adapter.generate(bundle, ...).
    """
    # Deterministic output based on hash so tests are repeatable
    h = hashlib.sha256(bundle.bundle_hash.encode()).hexdigest()[:8]
    proposed: Any
    if field_path == "body":
        proposed = f"[Proposed body for {artifact_type}] (run_hash={h})"
    elif "criteria" in field_path or "items" in field_path:
        proposed = [f"item-{h[:4]}", f"item-{h[4:8]}"]
    else:
        proposed = f"[Proposed {field_path}] (run_hash={h})"
    output_tokens = max(1, len(str(proposed)) // 4)
    return proposed, output_tokens


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_field(
    request: FieldRunRequest,
    *,
    bindings: list[FieldBinding],
    primary: ArtifactContext,
    parents: list[ArtifactContext] | None = None,
    siblings: list[ArtifactContext] | None = None,
    relations: list[ArtifactContext] | None = None,
) -> FieldRunResult | FieldRunError:
    """
    Execute a field run.

    Steps:
      1. Resolve the binding
      2. Check locks + cooldown
      3. Assemble context bundle
      4. Call model (stub)
      5. Validate proposal against OutputContract
      6. Return FieldRunResult (never apply patch)

    Returns FieldRunError on any rejection.
    """
    # 1. Resolve binding
    binding: FieldBinding | None
    if request.binding_id:
        binding = next((b for b in bindings if b.id == request.binding_id), None)
        if binding is None:
            return FieldRunError(
                run_id=request.run_id,
                code="BINDING_NOT_FOUND",
                message=f"Binding {request.binding_id!r} not found in registry",
            )
    else:
        binding = resolve_binding(
            bindings,
            artifact_type=request.artifact_type,
            field_path=request.field_path,
        )
        if binding is None:
            return FieldRunError(
                run_id=request.run_id,
                code="BINDING_NOT_FOUND",
                message=f"No binding found for {request.artifact_type}.{request.field_path}",
            )

    # 2a. Lock check
    if binding.policy.locked:
        return FieldRunError(
            run_id=request.run_id,
            code="FIELD_LOCKED",
            message=f"Field {request.field_path!r} is locked by binding policy",
            detail={"binding_id": binding.id},
        )

    # 2b. Cooldown check
    remaining = _check_cooldown(binding, request.artifact_id)
    if remaining is not None:
        return FieldRunError(
            run_id=request.run_id,
            code="COOLDOWN_ACTIVE",
            message=f"Binding {binding.id!r} is in cooldown for {remaining:.1f}s more",
            detail={"remaining_seconds": round(remaining, 2)},
        )

    # 3. Assemble context bundle
    try:
        bundle = assemble_context(
            binding=binding,
            primary=primary,
            parents=parents,
            siblings=siblings,
            relations=relations,
            system_instructions=request.system_instructions,
            jit_handles=request.jit_handles,
        )
    except Exception as exc:  # pragma: no cover
        return FieldRunError(
            run_id=request.run_id,
            code="CONTEXT_ERROR",
            message=f"Context assembly failed: {exc}",
        )

    input_tokens = bundle.total_tokens

    # 4. Model call (stub)
    proposed_value, output_tokens = _stub_model_call(
        bundle,
        field_path=request.field_path,
        artifact_type=request.artifact_type,
    )
    cost_tokens = input_tokens + output_tokens

    # 5. Validate proposal
    violations = _validate_against_contract(proposed_value, binding, request.field_path)
    schema_valid = len(violations) == 0

    if not schema_valid:
        return FieldRunError(
            run_id=request.run_id,
            code="SCHEMA_VIOLATION",
            message=f"Proposal failed OutputContract validation: {'; '.join(violations)}",
            detail={
                "violations": violations,
                "binding_id": binding.id,
                "cost_tokens": cost_tokens,
            },
        )

    # 6. Record cooldown + generate trace id
    _record_run(binding, request.artifact_id)
    trace_id = f"trace:{hashlib.sha256(f'{request.run_id}:{bundle.bundle_hash}'.encode()).hexdigest()[:16]}"

    can_auto_apply = binding.policy.auto_apply != AutoApplyPolicy.NEVER

    return FieldRunResult(
        run_id=request.run_id,
        binding_id=binding.id,
        artifact_id=request.artifact_id,
        field_path=request.field_path,
        proposal={request.field_path: proposed_value},
        schema_valid=True,
        cost_tokens=cost_tokens,
        trace_id=trace_id,
        bundle_hash=bundle.bundle_hash,
        can_auto_apply=can_auto_apply,
    )
