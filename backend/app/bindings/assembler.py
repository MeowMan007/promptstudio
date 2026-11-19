"""
TSK-041: Context assembler with token budget, redaction, and JIT handles.

Assembles the context bundle that gets sent to the model for a field run.
Guarantees:
  - same inputs → identical bundle hash (deterministic)
  - dropped items are reported (transparency)
  - secrets/PII are redacted per the binding's context_rule
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from backend.app.bindings.models import FieldBinding


# ---------------------------------------------------------------------------
# Context slice types
# ---------------------------------------------------------------------------

class SliceKind(str):
    ARTIFACT_BODY = "artifact_body"
    PARENT = "parent"
    SIBLING = "sibling"
    RELATION = "relation"
    SYSTEM = "system"
    JIT_HANDLE = "jit_handle"


@dataclass
class ContextSlice:
    kind: str
    source_id: str          # artifact_id or handle name
    content: str
    token_estimate: int
    redacted: bool = False
    redaction_reason: str | None = None


@dataclass
class DroppedSlice:
    kind: str
    source_id: str
    reason: str             # "budget_exceeded" | "redacted_fully" | "sensitivity_filter"
    token_estimate: int


@dataclass
class ContextBundle:
    binding_id: str
    artifact_id: str
    field_path: str
    slices: list[ContextSlice]
    dropped: list[DroppedSlice]
    total_tokens: int
    bundle_hash: str        # sha256 of deterministic serialisation


# ---------------------------------------------------------------------------
# Redaction
# ---------------------------------------------------------------------------

_REDACT_PLACEHOLDER = "[REDACTED]"


def _needs_redaction(content: str, sensitivity_tags: list[str]) -> bool:
    """Heuristic: check for sensitivity markers in the content."""
    low = content.lower()
    return any(tag.lower() in low for tag in sensitivity_tags)


def _redact(content: str) -> str:
    return _REDACT_PLACEHOLDER


# ---------------------------------------------------------------------------
# Token estimation (character-based approximation, 4 chars ≈ 1 token)
# ---------------------------------------------------------------------------

def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


# ---------------------------------------------------------------------------
# Assembler
# ---------------------------------------------------------------------------

@dataclass
class ArtifactContext:
    """Lightweight snapshot of an artifact passed to the assembler."""
    id: str
    type: str
    title: str
    body: str
    sensitivity: str | None = None
    tags: list[str] = field(default_factory=list)
    payload: dict[str, Any] = field(default_factory=dict)


def assemble_context(
    *,
    binding: FieldBinding,
    primary: ArtifactContext,
    parents: list[ArtifactContext] | None = None,
    siblings: list[ArtifactContext] | None = None,
    relations: list[ArtifactContext] | None = None,
    system_instructions: str | None = None,
    jit_handles: dict[str, str] | None = None,
) -> ContextBundle:
    """
    Build a ContextBundle from the binding's context_rule and the provided artifacts.
    Deterministic: same inputs always produce the same bundle_hash.
    """
    rule = binding.context_rule
    budget = rule.max_tokens
    used = 0
    slices: list[ContextSlice] = []
    dropped: list[DroppedSlice] = []

    def _add(kind: str, source_id: str, content: str, sensitivity: str | None = None) -> None:
        nonlocal used
        # Redaction check
        is_sensitive = (
            sensitivity in rule.redact_sensitivity
            or _needs_redaction(content, rule.redact_sensitivity)
        )
        redacted = False
        redaction_reason: str | None = None
        if is_sensitive:
            content = _redact(content)
            redacted = True
            redaction_reason = "sensitivity_filter"
            if content == _REDACT_PLACEHOLDER:
                # Fully redacted — still include the placeholder but mark it
                pass

        tokens = _estimate_tokens(content)
        if used + tokens > budget:
            dropped.append(DroppedSlice(kind=kind, source_id=source_id, reason="budget_exceeded", token_estimate=tokens))
            return
        used += tokens
        slices.append(ContextSlice(kind=kind, source_id=source_id, content=content, token_estimate=tokens, redacted=redacted, redaction_reason=redaction_reason))

    # 1. System instructions (highest priority, first in context)
    if system_instructions:
        _add(SliceKind.SYSTEM, "system", system_instructions)

    # 2. Primary artifact body
    if rule.include_artifact_body:
        body_content = f"# {primary.title}\n\n{primary.body}"
        if primary.payload:
            body_content += f"\n\n```json\n{json.dumps(primary.payload, indent=2)}\n```"
        _add(SliceKind.ARTIFACT_BODY, primary.id, body_content, primary.sensitivity)

    # 3. Parent chain
    if rule.include_parent_chain and parents:
        for parent in parents:
            _add(SliceKind.PARENT, parent.id, f"[parent] {parent.title}: {parent.body}", parent.sensitivity)

    # 4. Sibling types
    if rule.include_sibling_types and siblings:
        allowed_types = set(rule.include_sibling_types)
        for sib in siblings:
            if sib.type in allowed_types:
                _add(SliceKind.SIBLING, sib.id, f"[sibling/{sib.type}] {sib.title}: {sib.body}", sib.sensitivity)

    # 5. Relations
    if rule.include_relations and relations:
        allowed_rels = set(rule.include_relations)
        for rel in relations:
            if rel.type in allowed_rels:
                _add(SliceKind.RELATION, rel.id, f"[relation/{rel.type}] {rel.title}: {rel.body}", rel.sensitivity)

    # 6. JIT handles (resolved on demand, appended last)
    if jit_handles:
        for handle_name, handle_content in sorted(jit_handles.items()):
            _add(SliceKind.JIT_HANDLE, handle_name, f"[handle:{handle_name}]\n{handle_content}")

    # Compute deterministic hash
    canonical = json.dumps(
        {
            "binding_id": binding.id,
            "artifact_id": primary.id,
            "field_path": binding.field_path,
            "slices": [
                {"kind": s.kind, "source_id": s.source_id, "content": s.content}
                for s in slices
            ],
        },
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")

    bundle_hash = f"sha256:{hashlib.sha256(canonical).hexdigest()}"

    return ContextBundle(
        binding_id=binding.id,
        artifact_id=primary.id,
        field_path=binding.field_path,
        slices=slices,
        dropped=dropped,
        total_tokens=used,
        bundle_hash=bundle_hash,
    )
