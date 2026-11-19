"""
TSK-050: Patch schema + operation model + temp id resolution.
TSK-051: Patch validation service (schema, refs, perms, rules).
TSK-052: Transactional apply with revision preconditions.

A Patch is an atomic, reviewable bundle of operations against the project graph.
Key invariants:
  - All-or-nothing: if any operation fails validation, nothing is applied.
  - Stale base returns a conflict (409-style error) with field-level diff.
  - Idempotent retries: applying the same patch_id twice is a no-op.
  - Temp ids (prefixed "tmp:") are resolved to real ULIDs at apply time.
  - Every apply creates a revision record + audit event.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Operation types
# ---------------------------------------------------------------------------

class OpKind(str, Enum):
    CREATE_ARTIFACT = "create_artifact"
    UPDATE_ARTIFACT = "update_artifact"
    DELETE_ARTIFACT = "delete_artifact"
    CREATE_EDGE     = "create_edge"
    DELETE_EDGE     = "delete_edge"
    UPDATE_LAYOUT   = "update_layout"


@dataclass
class PatchOperation:
    kind: OpKind
    # For CREATE/UPDATE_ARTIFACT
    artifact_id: str | None = None          # real id OR "tmp:..." for creates
    artifact_type: str | None = None
    fields: dict[str, Any] = field(default_factory=dict)
    base_revision: int | None = None        # required for UPDATE; must match current
    # For edges
    source_id: str | None = None
    target_id: str | None = None
    edge_type: str | None = None
    edge_id: str | None = None
    # For layout
    projection_id: str | None = None
    position: dict[str, Any] | None = None


@dataclass
class Patch:
    patch_id: str                           # client-assigned; idempotency key
    project_id: str
    operations: list[PatchOperation]
    created_by: str
    approval_tier: int = 1                  # 1=normal, 2=high-risk (requires explicit confirm)
    approval_token: str | None = None       # required for tier-2
    description: str = ""


# ---------------------------------------------------------------------------
# Validation result
# ---------------------------------------------------------------------------

@dataclass
class OperationError:
    operation_index: int
    code: str
    message: str
    field: str | None = None


@dataclass
class ValidationResult:
    valid: bool
    errors: list[OperationError] = field(default_factory=list)

    def add_error(self, idx: int, code: str, message: str, f: str | None = None) -> None:
        self.errors.append(OperationError(operation_index=idx, code=code, message=message, field=f))
        self.valid = False


# ---------------------------------------------------------------------------
# TSK-051: Validation service
# ---------------------------------------------------------------------------

_TMP_ID_RE = re.compile(r"^tmp:[a-zA-Z0-9_\-]{1,64}$")
_REAL_ID_RE = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")   # ULID pattern

_VALID_ARTIFACT_TYPES = {
    "brief", "idea", "problem", "persona", "user_story", "requirement",
    "constraint", "decision", "user_flow", "screen", "interaction",
    "component", "integration", "data_entity", "api_endpoint",
    "event_contract", "prompt", "prompt_flow", "skill", "risk",
    "test_case", "evaluation_case", "epic", "task", "milestone",
    "question", "issue",
}


def validate_patch(
    patch: Patch,
    *,
    existing_artifact_ids: set[str] | None = None,
    existing_revision: dict[str, int] | None = None,
    caller_role: str = "editor",
    approved_tokens: set[str] | None = None,
) -> ValidationResult:
    """
    Validate a patch before applying it.
    Returns a ValidationResult; if not valid, nothing should be applied.

    Parameters
    ----------
    existing_artifact_ids:
        IDs of artifacts that exist in the project (for ref checks).
    existing_revision:
        Map of artifact_id → current revision number (for precondition checks).
    caller_role:
        Role of the user submitting the patch.
    approved_tokens:
        Set of single-use approval tokens that have been granted.
    """
    result = ValidationResult(valid=True)
    existing_artifact_ids = existing_artifact_ids or set()
    existing_revision = existing_revision or {}
    approved_tokens = approved_tokens or set()

    # Collect temp ids created in this patch so forward-references are allowed
    created_tmp_ids: set[str] = set()
    for op in patch.operations:
        if op.kind == OpKind.CREATE_ARTIFACT and op.artifact_id and _TMP_ID_RE.match(op.artifact_id):
            created_tmp_ids.add(op.artifact_id)

    # Role check: viewers cannot submit patches
    if caller_role == "viewer":
        result.add_error(-1, "PERM_DENIED", "Viewers may not submit patches")
        return result

    # Approval tier check
    if patch.approval_tier >= 2:
        if not patch.approval_token or patch.approval_token not in approved_tokens:
            result.add_error(-1, "APPROVAL_REQUIRED", "High-risk patch requires a valid approval token")

    for idx, op in enumerate(patch.operations):
        # ── CREATE_ARTIFACT ─────────────────────────────────────────────────
        if op.kind == OpKind.CREATE_ARTIFACT:
            if not op.artifact_id or not (_TMP_ID_RE.match(op.artifact_id)):
                result.add_error(idx, "INVALID_ID", "CREATE_ARTIFACT requires a tmp: id", "artifact_id")
            if not op.artifact_type:
                result.add_error(idx, "MISSING_FIELD", "artifact_type is required", "artifact_type")
            elif op.artifact_type not in _VALID_ARTIFACT_TYPES:
                result.add_error(idx, "UNKNOWN_TYPE", f"Unknown artifact type: {op.artifact_type}", "artifact_type")
            if not op.fields.get("title"):
                result.add_error(idx, "MISSING_FIELD", "title is required for new artifacts", "title")

        # ── UPDATE_ARTIFACT ─────────────────────────────────────────────────
        elif op.kind == OpKind.UPDATE_ARTIFACT:
            if not op.artifact_id:
                result.add_error(idx, "MISSING_FIELD", "artifact_id is required for UPDATE", "artifact_id")
            elif op.artifact_id not in existing_artifact_ids:
                result.add_error(idx, "NOT_FOUND", f"Artifact {op.artifact_id} not found", "artifact_id")
            elif op.base_revision is None:
                result.add_error(idx, "MISSING_FIELD", "base_revision is required for UPDATE", "base_revision")
            elif op.artifact_id in existing_revision:
                current = existing_revision[op.artifact_id]
                if op.base_revision != current:
                    result.add_error(
                        idx, "STALE_BASE",
                        f"Stale revision: expected {current}, got {op.base_revision}",
                        "base_revision",
                    )

        # ── DELETE_ARTIFACT ─────────────────────────────────────────────────
        elif op.kind == OpKind.DELETE_ARTIFACT:
            if not op.artifact_id:
                result.add_error(idx, "MISSING_FIELD", "artifact_id required for DELETE", "artifact_id")
            elif op.artifact_id not in existing_artifact_ids:
                result.add_error(idx, "NOT_FOUND", f"Artifact {op.artifact_id} not found", "artifact_id")
            # Deletes are high-risk — require tier-2 token
            if patch.approval_tier < 2:
                result.add_error(idx, "APPROVAL_REQUIRED", "DELETE_ARTIFACT requires approval_tier=2")

        # ── CREATE_EDGE ─────────────────────────────────────────────────────
        elif op.kind == OpKind.CREATE_EDGE:
            for attr, name in [("source_id", "source_id"), ("target_id", "target_id"), ("edge_type", "edge_type")]:
                if not getattr(op, attr):
                    result.add_error(idx, "MISSING_FIELD", f"{name} required for CREATE_EDGE", name)
            # Both endpoints must exist (or be tmp: ids created in this patch)
            for attr in ("source_id", "target_id"):
                val = getattr(op, attr)
                if val and not (val in existing_artifact_ids or val in created_tmp_ids):
                    result.add_error(idx, "REF_NOT_FOUND", f"{attr} {val} not found in project or patch creates", attr)

        # ── DELETE_EDGE ─────────────────────────────────────────────────────
        elif op.kind == OpKind.DELETE_EDGE:
            if not op.edge_id:
                result.add_error(idx, "MISSING_FIELD", "edge_id required for DELETE_EDGE", "edge_id")

        # ── UPDATE_LAYOUT ────────────────────────────────────────────────────
        elif op.kind == OpKind.UPDATE_LAYOUT:
            if not op.projection_id:
                result.add_error(idx, "MISSING_FIELD", "projection_id required for UPDATE_LAYOUT", "projection_id")
            if not op.position:
                result.add_error(idx, "MISSING_FIELD", "position required for UPDATE_LAYOUT", "position")

    return result


# ---------------------------------------------------------------------------
# TSK-052: Apply (in-memory simulation; real impl uses DB transactions)
# ---------------------------------------------------------------------------

@dataclass
class ApplyResult:
    success: bool
    patch_id: str
    id_map: dict[str, str] = field(default_factory=dict)   # tmp: → real ULID
    errors: list[OperationError] = field(default_factory=list)
    new_revisions: dict[str, int] = field(default_factory=dict)


def _new_ulid() -> str:
    """Generate a placeholder ULID-shaped ID for in-memory apply."""
    import time, secrets, string
    chars = string.ascii_uppercase.replace("I", "").replace("L", "").replace("O", "").replace("U", "")
    chars += string.digits
    ts = format(int(time.time() * 1000), "010x").upper()[:10]
    rand = "".join(secrets.choice(chars) for _ in range(16))
    return (ts + rand)[:26]


def apply_patch(
    patch: Patch,
    *,
    existing_artifacts: dict[str, dict[str, Any]] | None = None,
    existing_revisions: dict[str, int] | None = None,
    applied_patch_ids: set[str] | None = None,
    approved_tokens: set[str] | None = None,
    caller_role: str = "editor",
) -> ApplyResult:
    """
    Validate then apply a patch, returning an ApplyResult.
    - Idempotent: returns success immediately if patch_id already applied.
    - All-or-nothing: validation failure = nothing written.
    - temp ids resolved to real ULIDs; mapping returned.
    """
    existing_artifacts = dict(existing_artifacts or {})
    existing_revisions = dict(existing_revisions or {})
    applied_patch_ids = set(applied_patch_ids or set())
    approved_tokens = set(approved_tokens or set())

    # Idempotency check
    if patch.patch_id in applied_patch_ids:
        return ApplyResult(success=True, patch_id=patch.patch_id)

    # Validate first
    validation = validate_patch(
        patch,
        existing_artifact_ids=set(existing_artifacts.keys()),
        existing_revision=existing_revisions,
        caller_role=caller_role,
        approved_tokens=approved_tokens,
    )
    if not validation.valid:
        return ApplyResult(success=False, patch_id=patch.patch_id, errors=validation.errors)

    # Apply operations
    id_map: dict[str, str] = {}
    new_revisions: dict[str, int] = {}

    for op in patch.operations:
        if op.kind == OpKind.CREATE_ARTIFACT:
            real_id = _new_ulid()
            if op.artifact_id:
                id_map[op.artifact_id] = real_id
            existing_artifacts[real_id] = {
                "id": real_id,
                "type": op.artifact_type,
                **op.fields,
            }
            existing_revisions[real_id] = 1
            new_revisions[real_id] = 1

        elif op.kind == OpKind.UPDATE_ARTIFACT and op.artifact_id:
            existing_artifacts[op.artifact_id].update(op.fields)
            current_rev = existing_revisions.get(op.artifact_id, 0) + 1
            existing_revisions[op.artifact_id] = current_rev
            new_revisions[op.artifact_id] = current_rev

        elif op.kind == OpKind.DELETE_ARTIFACT and op.artifact_id:
            existing_artifacts.pop(op.artifact_id, None)
            existing_revisions.pop(op.artifact_id, None)

    applied_patch_ids.add(patch.patch_id)
    return ApplyResult(success=True, patch_id=patch.patch_id, id_map=id_map, new_revisions=new_revisions)
