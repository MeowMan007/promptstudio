from __future__ import annotations

# ruff: noqa: E501
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from backend.app.ids import alias_prefix_for_type

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "fixtures" / "golden"
FIXTURE_TIME = datetime(2026, 1, 1, tzinfo=UTC).isoformat()

PROJECTS: list[dict[str, Any]] = [
    {
        "slug": "creator-payments",
        "name": "Creator Payment Forms",
        "kind": "saas",
        "summary": "Creators collect reliable payments through hosted forms.",
        "requirement": "A creator can publish a payment form and review completed payments.",
        "screen": ("Payment Form", "/payments/new", "Configure and publish a payment form."),
        "component": "Payment Form Service",
        "entity": "Payment",
        "endpoint": ("POST", "/api/payments"),
        "prompt": "Payment Form Review",
        "skill": "payment-form-review",
        "task": "Build hosted payment form",
        "export": [
            "AGENTS.md",
            "spec.md",
            "contracts/payment.json",
            "prompts/payment-review.md",
            "skills/payment-form-review/SKILL.md",
        ],
    },
    {
        "slug": "internal-admin",
        "name": "Internal Admin Tool",
        "kind": "crud",
        "summary": "Operators review and update customer records with an audit trail.",
        "requirement": "An operator can find, inspect, update, and audit a customer record.",
        "screen": ("Customer Directory", "/customers", "Search and manage customer records."),
        "component": "Customer Admin API",
        "entity": "Customer",
        "endpoint": ("PATCH", "/api/customers/{customer_id}"),
        "prompt": "Customer Record Review",
        "skill": "customer-record-review",
        "task": "Build customer directory",
        "export": [
            "AGENTS.md",
            "spec.md",
            "contracts/customer.json",
            "prompts/customer-review.md",
            "skills/customer-record-review/SKILL.md",
        ],
    },
    {
        "slug": "data-pipeline",
        "name": "Daily Data Pipeline",
        "kind": "batch",
        "summary": "A daily batch imports, validates, and publishes partner data.",
        "requirement": "The pipeline imports each partner batch once and reports rejected rows.",
        "screen": ("Pipeline Runs", "/pipeline/runs", "Inspect batch runs and rejected rows."),
        "component": "Partner Import Worker",
        "entity": "Partner Row",
        "endpoint": ("POST", "/api/pipeline/runs"),
        "prompt": "Rejected Row Triage",
        "skill": "pipeline-row-triage",
        "task": "Build partner import pipeline",
        "export": [
            "AGENTS.md",
            "spec.md",
            "contracts/partner-row.json",
            "prompts/row-triage.md",
            "skills/pipeline-row-triage/SKILL.md",
        ],
    },
]


def make_project(definition: dict[str, Any], project_number: int) -> dict[str, Any]:
    project_id = f"prj_{project_number:026d}"
    artifacts: list[dict[str, Any]] = []
    alias_counts: dict[str, int] = {}
    artifact_number = 0

    def add(artifact_type: str, title: str, payload: dict[str, Any], body: str = "") -> str:
        nonlocal artifact_number
        artifact_number += 1
        prefix = alias_prefix_for_type(artifact_type)
        alias_counts[prefix] = alias_counts.get(prefix, 0) + 1
        artifact_id = f"art_{artifact_number:026d}"
        artifacts.append(
            {
                "id": artifact_id,
                "alias": f"{prefix}-{alias_counts[prefix]:03d}",
                "project_id": project_id,
                "type": artifact_type,
                "schema_version": "1.0.0",
                "title": title,
                "body": body,
                "payload": payload,
                "status": "proposed",
                "revision": 1,
                "created_by": "golden-fixture",
                "updated_by": "golden-fixture",
                "visibility": "project",
                "sensitivity": "internal",
                "provenance": {"origin": "user_input"},
                "created_at": FIXTURE_TIME,
                "updated_at": FIXTURE_TIME,
            }
        )
        return artifact_id

    brief_id = add(
        "brief",
        definition["name"],
        {"summary": definition["summary"], "raw_input": definition["summary"]},
    )
    requirement_id = add(
        "requirement",
        definition["requirement"],
        {
            "ears_pattern": "ubiquitous",
            "clauses": {"response": definition["requirement"]},
            "priority": "should",
            "acceptance_criteria": [
                {
                    "id": "AC-1",
                    "given": "the user is authorized",
                    "when": "the operation completes",
                    "then": "the result is recorded",
                }
            ],
        },
    )
    screen_name, route, purpose = definition["screen"]
    screen_id = add(
        "screen",
        screen_name,
        {
            "name": screen_name,
            "route": route,
            "purpose": purpose,
            "regions": [{"id": "main", "elements": ["primary-action"]}],
            "elements": [
                {
                    "id": "primary-action",
                    "component": "button",
                    "label": "Continue",
                    "required": True,
                }
            ],
            "states": ["empty", "loading", "error", "success"],
        },
    )
    entity_id = add(
        "data_entity",
        definition["entity"],
        {"name": definition["entity"], "fields": ["id", "created_at"], "keys": ["id"]},
    )
    component_id = add(
        "component",
        definition["component"],
        {
            "name": definition["component"],
            "responsibility": definition["summary"],
            "interfaces": ["http"],
        },
    )
    method, path = definition["endpoint"]
    endpoint_id = add(
        "api_endpoint",
        f"{method} {path}",
        {
            "method": method,
            "path": path,
            "auth": "signed-in user",
            "request": {"content_type": "application/json"},
            "response": {"content_type": "application/json"},
            "errors": {"400": "invalid request", "401": "unauthorized"},
            "data_entities": [entity_id],
        },
    )
    evaluation_id = add(
        "evaluation_case",
        f"{definition['prompt']} evaluation",
        {
            "input": "Review this project context.",
            "expected_or_rubric": "Return a concise, schema-valid review.",
        },
    )
    prompt_id = add(
        "prompt",
        definition["prompt"],
        {
            "name": definition["prompt"],
            "blocks": [
                {
                    "block_type": "instruction",
                    "content": "Review the supplied project context and return actionable findings.",
                }
            ],
            "output_contract": {"type": "object", "required": ["findings"]},
            "evaluation_case_ids": [evaluation_id],
        },
    )
    skill_id = add(
        "skill",
        definition["skill"],
        {
            "name": definition["skill"],
            "version": "1.0.0",
            "content_hash": "sha256:golden-fixture",
            "trust": "user",
            "directory_name": definition["skill"],
            "frontmatter": {
                "name": definition["skill"],
                "description": f"Review {definition['kind']} project artifacts.",
                "allowed_tools": ["read_project"],
            },
            "granted_tools": ["read_project"],
        },
    )
    task_id = add(
        "task",
        definition["task"],
        {
            "title": definition["task"],
            "acceptance_criteria": ["The primary workflow completes and records its result."],
            "depends_on": [],
            "deliverable_ids": [screen_id, component_id, endpoint_id],
        },
    )
    flow_id = add(
        "user_flow",
        f"{definition['name']} primary flow",
        {
            "name": f"{definition['name']} primary flow",
            "steps": [{"label": "Complete the primary workflow", "screen_id": screen_id}],
        },
    )
    decision_id = add(
        "decision",
        "Use a typed, auditable artifact graph",
        {
            "chosen_option": "typed graph",
            "alternatives": ["unstructured notes"],
            "rationale": "The graph supports validation and reproducible exports.",
            "consequences": ["Artifacts use versioned contracts."],
        },
    )
    edges = [
        {
            "id": f"edge_{index:03d}",
            "project_id": project_id,
            "source_id": source,
            "target_id": target,
            "edge_type": edge_type,
            "metadata": {},
        }
        for index, (source, target, edge_type) in enumerate(
            [
                (component_id, requirement_id, "implements"),
                (component_id, endpoint_id, "calls"),
                (endpoint_id, entity_id, "reads"),
                (screen_id, endpoint_id, "calls"),
                (prompt_id, skill_id, "uses_skill"),
                (flow_id, screen_id, "contains"),
                (task_id, requirement_id, "depends_on"),
                (brief_id, requirement_id, "derived_from"),
                (decision_id, requirement_id, "relates_to"),
            ],
            start=1,
        )
    ]
    return {
        "fixture_schema_version": "1.0.0",
        "project": {
            "id": project_id,
            "slug": definition["slug"],
            "name": definition["name"],
            "current_revision": 1,
        },
        "artifacts": artifacts,
        "edges": edges,
        "expected_export": {"format": "prompt-studio-project@1.0.0", "files": definition["export"]},
    }


def main() -> None:
    FIXTURE_ROOT.mkdir(parents=True, exist_ok=True)
    for project_number, definition in enumerate(PROJECTS, start=1):
        target = FIXTURE_ROOT / f"{definition['slug']}.json"
        target.write_text(
            json.dumps(make_project(definition, project_number), indent=2) + "\n", encoding="utf-8"
        )
        print(target.relative_to(ROOT))


if __name__ == "__main__":
    main()
