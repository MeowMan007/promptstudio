"""
TSK-044: Built-in field prompt catalogue (14 bindings).

Each entry is a FieldBinding at TYPE_DEFAULT scope covering the main
artifact types in Prompt Studio. Each binding includes:
  - context_rule: what context slices to include
  - output_contract: schema + required fields
  - policy: sensible defaults

This module also exposes:
  - CATALOGUE: list of all 14 built-in FieldBinding objects
  - get_binding(artifact_type, field_path): look up a built-in binding
  - smoke_test_binding(binding): run a lightweight correctness check
"""
from __future__ import annotations

from backend.app.bindings.models import (
    AutoApplyPolicy,
    BindingPolicy,
    BindingScope,
    ContextRule,
    FieldBinding,
    OutputContract,
)


def _b(
    bid: str,
    artifact_type: str,
    field_path: str,
    *,
    prompt_asset_id: str,
    max_tokens: int = 8192,
    include_parent_chain: bool = True,
    include_siblings: list[str] | None = None,
    include_relations: list[str] | None = None,
    schema_type: str = "string",
    required_fields: list[str] | None = None,
    max_array_length: dict[str, int] | None = None,
    auto_apply: AutoApplyPolicy = AutoApplyPolicy.NEVER,
    cooldown: int = 0,
    locked: bool = False,
) -> FieldBinding:
    return FieldBinding(
        id=bid,
        artifact_type=artifact_type,
        field_path=field_path,
        scope=BindingScope.TYPE_DEFAULT,
        scope_id="*",
        prompt_asset_id=prompt_asset_id,
        context_rule=ContextRule(
            include_artifact_body=True,
            include_parent_chain=include_parent_chain,
            include_sibling_types=include_siblings or [],
            include_relations=include_relations or [],
            max_tokens=max_tokens,
        ),
        output_contract=OutputContract(
            json_schema={"type": schema_type},
            required_fields=required_fields or [],
            max_array_length=max_array_length or {},
        ),
        policy=BindingPolicy(
            locked=locked,
            cooldown_seconds=cooldown,
            auto_apply=auto_apply,
        ),
    )


# ---------------------------------------------------------------------------
# 14 built-in bindings
# ---------------------------------------------------------------------------

CATALOGUE: list[FieldBinding] = [
    # 1. Brief → body
    _b("builtin:brief:body", "brief", "body",
       prompt_asset_id="pa:brief-body",
       include_siblings=["idea", "problem"],
       schema_type="string"),

    # 2. Persona → body (biography + goals)
    _b("builtin:persona:body", "persona", "body",
       prompt_asset_id="pa:persona-body",
       schema_type="string",
       include_siblings=["brief"]),

    # 3. User Story → body
    _b("builtin:user_story:body", "user_story", "body",
       prompt_asset_id="pa:user-story-body",
       include_siblings=["persona", "epic"],
       schema_type="string",
       cooldown=30),

    # 4. User Story → acceptance_criteria (array of strings)
    _b("builtin:user_story:acceptance_criteria",
       "user_story", "payload.acceptance_criteria",
       prompt_asset_id="pa:user-story-ac",
       include_siblings=["persona", "epic"],
       schema_type="array",
       max_array_length={"payload.acceptance_criteria": 10},
       cooldown=30),

    # 5. Requirement → body
    _b("builtin:requirement:body", "requirement", "body",
       prompt_asset_id="pa:requirement-body",
       include_siblings=["brief", "constraint"],
       schema_type="string"),

    # 6. Constraint → body
    _b("builtin:constraint:body", "constraint", "body",
       prompt_asset_id="pa:constraint-body",
       include_siblings=["brief", "requirement"],
       schema_type="string"),

    # 7. Decision → body (ADR body)
    _b("builtin:decision:body", "decision", "body",
       prompt_asset_id="pa:decision-body",
       include_siblings=["requirement", "constraint"],
       schema_type="string"),

    # 8. User Flow → body (step-by-step narrative)
    _b("builtin:user_flow:body", "user_flow", "body",
       prompt_asset_id="pa:user-flow-body",
       include_siblings=["persona", "user_story"],
       schema_type="string"),

    # 9. Screen → body (wireframe description)
    _b("builtin:screen:body", "screen", "body",
       prompt_asset_id="pa:screen-body",
       include_siblings=["user_flow", "component"],
       schema_type="string"),

    # 10. API Endpoint → body (spec / OpenAPI snippet)
    _b("builtin:api_endpoint:body", "api_endpoint", "body",
       prompt_asset_id="pa:api-endpoint-body",
       include_siblings=["data_entity", "event_contract"],
       schema_type="string"),

    # 11. Data Entity → body (schema / ER description)
    _b("builtin:data_entity:body", "data_entity", "body",
       prompt_asset_id="pa:data-entity-body",
       include_siblings=["api_endpoint"],
       schema_type="string"),

    # 12. Risk → body (risk description + mitigations)
    _b("builtin:risk:body", "risk", "body",
       prompt_asset_id="pa:risk-body",
       include_siblings=["requirement", "decision"],
       schema_type="string"),

    # 13. Test Case → body (gherkin / test steps)
    _b("builtin:test_case:body", "test_case", "body",
       prompt_asset_id="pa:test-case-body",
       include_siblings=["user_story", "requirement"],
       schema_type="string",
       cooldown=15),

    # 14. Evaluation Case → body (eval question + rubric)
    _b("builtin:evaluation_case:body", "evaluation_case", "body",
       prompt_asset_id="pa:eval-case-body",
       include_siblings=["prompt", "test_case"],
       schema_type="string"),
]

assert len(CATALOGUE) == 14, f"Expected 14 built-in bindings, got {len(CATALOGUE)}"

# Index for fast lookup
_INDEX: dict[tuple[str, str], FieldBinding] = {
    (b.artifact_type, b.field_path): b for b in CATALOGUE
}


def get_binding(artifact_type: str, field_path: str) -> FieldBinding | None:
    """Return the built-in binding for (artifact_type, field_path), or None."""
    return _INDEX.get((artifact_type, field_path))


# ---------------------------------------------------------------------------
# Smoke test helper (TSK-044 acceptance: each binding has a passing smoke test)
# ---------------------------------------------------------------------------

def smoke_test_binding(binding: FieldBinding) -> list[str]:
    """
    Run lightweight correctness checks on a single binding.
    Returns list of failure strings (empty = pass).
    """
    failures: list[str] = []

    if not binding.id:
        failures.append("id is empty")
    if not binding.artifact_type:
        failures.append("artifact_type is empty")
    if not binding.field_path:
        failures.append("field_path is empty")
    if not binding.prompt_asset_id:
        failures.append("prompt_asset_id is empty")
    if binding.scope != BindingScope.TYPE_DEFAULT:
        failures.append(f"expected TYPE_DEFAULT scope, got {binding.scope}")
    if binding.context_rule.max_tokens <= 0:
        failures.append("max_tokens must be > 0")
    if binding.output_contract.json_schema.get("type") not in {"string", "array", "object"}:
        failures.append(f"unsupported schema type: {binding.output_contract.json_schema.get('type')}")

    return failures
