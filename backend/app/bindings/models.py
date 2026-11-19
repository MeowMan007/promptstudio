"""
TSK-040: FieldBinding model + inheritance resolution.

Binding priority (low → high, later overrides earlier):
  type_default → project → artifact → run

A binding defines HOW a model fills a specific field on a specific artifact type:
  - context_rule: what to include in the context window
  - output_contract: Pydantic/JSON schema the output must satisfy
  - policy: locks, cooldowns, auto_apply restrictions
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class BindingScope(str, Enum):
    TYPE_DEFAULT = "type_default"
    PROJECT = "project"
    ARTIFACT = "artifact"
    RUN = "run"


class AutoApplyPolicy(str, Enum):
    """Controls whether the agent can apply its own proposal without human review."""
    NEVER = "never"       # always requires human approval
    LOW_RISK = "low_risk" # auto-apply when output passes all schema + eval checks
    ALWAYS = "always"     # auto-apply unconditionally (restricted to trusted skills)


@dataclass
class ContextRule:
    """Declares what context slices to include when assembling the prompt."""
    include_artifact_body: bool = True
    include_parent_chain: bool = True
    include_sibling_types: list[str] = field(default_factory=list)
    include_relations: list[str] = field(default_factory=list)
    max_tokens: int = 8192
    redact_sensitivity: list[str] = field(default_factory=lambda: ["secret", "pii"])


@dataclass
class OutputContract:
    """The schema the model output must satisfy before it can be proposed as a patch."""
    json_schema: dict[str, Any] = field(default_factory=dict)
    required_fields: list[str] = field(default_factory=list)
    forbidden_fields: list[str] = field(default_factory=list)
    max_array_length: dict[str, int] = field(default_factory=dict)


@dataclass
class BindingPolicy:
    locked: bool = False
    cooldown_seconds: int = 0
    auto_apply: AutoApplyPolicy = AutoApplyPolicy.NEVER
    require_approver_role: str = "reviewer"


@dataclass
class FieldBinding:
    """
    A binding wires a model run to a specific field of a specific artifact type.
    Multiple bindings at different scopes are resolved by priority.
    """
    id: str
    artifact_type: str
    field_path: str           # e.g. "body", "payload.acceptance_criteria"
    scope: BindingScope
    scope_id: str             # project_id / artifact_id / run_id depending on scope
    prompt_asset_id: str      # reference to the prompt asset to use
    context_rule: ContextRule = field(default_factory=ContextRule)
    output_contract: OutputContract = field(default_factory=OutputContract)
    policy: BindingPolicy = field(default_factory=BindingPolicy)
    revision: int = 1


# ---------------------------------------------------------------------------
# Inheritance resolution
# ---------------------------------------------------------------------------

_SCOPE_PRIORITY: dict[BindingScope, int] = {
    BindingScope.TYPE_DEFAULT: 0,
    BindingScope.PROJECT: 1,
    BindingScope.ARTIFACT: 2,
    BindingScope.RUN: 3,
}


def resolve_binding(
    bindings: list[FieldBinding],
    artifact_type: str,
    field_path: str,
    *,
    project_id: str | None = None,
    artifact_id: str | None = None,
    run_id: str | None = None,
) -> FieldBinding | None:
    """
    Given a list of bindings, return the highest-priority one that applies to
    the given artifact_type + field_path combination.

    Resolution order (ascending priority):
        type_default → project → artifact → run
    """
    candidates: list[FieldBinding] = []

    for b in bindings:
        if b.artifact_type != artifact_type or b.field_path != field_path:
            continue
        # Check scope applicability
        if b.scope == BindingScope.TYPE_DEFAULT:
            candidates.append(b)
        elif b.scope == BindingScope.PROJECT and project_id and b.scope_id == project_id:
            candidates.append(b)
        elif b.scope == BindingScope.ARTIFACT and artifact_id and b.scope_id == artifact_id:
            candidates.append(b)
        elif b.scope == BindingScope.RUN and run_id and b.scope_id == run_id:
            candidates.append(b)

    if not candidates:
        return None

    # Return the highest-priority (highest scope value) candidate.
    # Ties broken by revision (higher revision wins).
    return max(candidates, key=lambda b: (_SCOPE_PRIORITY[b.scope], b.revision))


def merge_bindings(lower: FieldBinding, higher: FieldBinding) -> FieldBinding:
    """
    Merge two bindings where `higher` overrides `lower`.
    Only non-default scalar values in `higher` override `lower`.
    This enables partial overrides at the project/artifact level.
    """
    import copy
    merged = copy.deepcopy(lower)

    # Policy: higher wins on explicit non-default values
    if higher.policy.locked:
        merged.policy.locked = True
    if higher.policy.cooldown_seconds > 0:
        merged.policy.cooldown_seconds = higher.policy.cooldown_seconds
    if higher.policy.auto_apply != AutoApplyPolicy.NEVER:
        merged.policy.auto_apply = higher.policy.auto_apply
    if higher.policy.require_approver_role != "reviewer":
        merged.policy.require_approver_role = higher.policy.require_approver_role

    # Context rule: higher wins on non-default values
    if not higher.context_rule.include_artifact_body:
        merged.context_rule.include_artifact_body = False
    if higher.context_rule.max_tokens != 8192:
        merged.context_rule.max_tokens = higher.context_rule.max_tokens
    if higher.context_rule.sibling_types if hasattr(higher.context_rule, 'sibling_types') else higher.context_rule.include_sibling_types:
        merged.context_rule.include_sibling_types = higher.context_rule.include_sibling_types
    if higher.context_rule.redact_sensitivity != ["secret", "pii"]:
        merged.context_rule.redact_sensitivity = higher.context_rule.redact_sensitivity

    # Prompt asset: higher always wins if set
    if higher.prompt_asset_id:
        merged.prompt_asset_id = higher.prompt_asset_id

    merged.scope = higher.scope
    merged.scope_id = higher.scope_id
    merged.revision = higher.revision
    return merged
