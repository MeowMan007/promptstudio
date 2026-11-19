from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from prompt_studio_api.contracts.registry import load_type_registry
from prompt_studio_api.validation import ValidationContext, validate_project

from backend.app.ids import (
    alias_prefix_for_type,
    new_artifact_id,
    new_project_id,
    new_ulid,
)

ROOT = Path(__file__).resolve().parents[2]
CASES = json.loads((ROOT / "fixtures" / "validation" / "rule_cases.json").read_text())["cases"]


def case_context(scenario: str) -> ValidationContext:
    project_id = new_project_id()
    artifacts: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    counters: dict[str, int] = {}
    now = datetime.now(UTC).isoformat()

    def artifact(artifact_type: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        definition = load_type_registry().types[artifact_type]
        values: dict[str, Any] = {field: "value" for field in definition.required}
        if artifact_type == "requirement":
            values.update(
                {
                    "ears_pattern": "ubiquitous",
                    "clauses": {"response": "The system saves the result."},
                    "priority": "should",
                    "acceptance_criteria": [],
                }
            )
        elif artifact_type == "screen":
            values.update(
                {
                    "name": "Screen",
                    "route": "/screen",
                    "purpose": "Test",
                    "regions": [],
                    "elements": [],
                    "states": ["empty", "loading", "error", "success"],
                }
            )
        if payload:
            values.update(payload)
        prefix = alias_prefix_for_type(artifact_type)
        counters[prefix] = counters.get(prefix, 0) + 1
        record = {
            "id": new_artifact_id(),
            "alias": f"{prefix}-{counters[prefix]:03d}",
            "project_id": project_id,
            "type": artifact_type,
            "schema_version": "1.0.0",
            "title": f"{artifact_type} fixture",
            "body": "",
            "payload": values,
            "status": "scratch",
            "revision": 1,
            "created_by": "test-user",
            "updated_by": "test-user",
            "visibility": "project",
            "sensitivity": "internal",
            "provenance": {"origin": "user_input"},
            "created_at": now,
            "updated_at": now,
        }
        artifacts.append(record)
        return record

    def edge(
        source: str, target: str, edge_type: str, metadata: dict[str, Any] | None = None
    ) -> None:
        edges.append(
            {
                "id": new_ulid(),
                "project_id": project_id,
                "source_id": source,
                "target_id": target,
                "edge_type": edge_type,
                "metadata": metadata or {},
            }
        )

    project_revisions = [1]
    export_target_revision: int | None = 1
    diagram_source_edges: list[dict[str, str]] = []
    projections: list[dict[str, Any]] = []

    if scenario == "invalid_payload_schema":
        record = artifact("requirement")
        record["payload"] = {"ears_pattern": "not-a-pattern"}
    elif scenario == "duplicate_project_alias":
        first = artifact("idea", {"content": "One"})
        second = artifact("idea", {"content": "Two"})
        second["alias"] = first["alias"]
    elif scenario == "unresolved_edge_endpoint":
        source = artifact("idea", {"content": "One"})
        edge(source["id"], "art_01JG7Z3M8Q9XR4T2V6B0N5K1D9", "derived_from")
    elif scenario == "disallowed_edge_pair":
        source = artifact("idea", {"content": "One"})
        target = artifact("task", {"title": "T", "acceptance_criteria": [], "depends_on": []})
        edge(source["id"], target["id"], "depends_on")
    elif scenario == "dependency_cycle":
        one = artifact("task", {"title": "A", "acceptance_criteria": [], "depends_on": []})
        two = artifact("task", {"title": "B", "acceptance_criteria": [], "depends_on": []})
        edge(one["id"], two["id"], "depends_on")
        edge(two["id"], one["id"], "depends_on")
    elif scenario in {"approved_must_without_acceptance", "approved_requirement_without_test"}:
        payload = {
            "priority": "must" if scenario == "approved_must_without_acceptance" else "should"
        }
        record = artifact("requirement", payload)
        record["status"] = "approved"
        if scenario == "approved_requirement_without_test":
            record["payload"]["acceptance_criteria"] = [
                {"id": "AC-1", "given": "a user", "when": "saved", "then": "it persists"}
            ]
    elif scenario == "component_without_implementation":
        artifact("component", {"name": "C", "responsibility": "R", "interfaces": []})
    elif scenario in {"api_without_component_or_contract", "unknown_data_entity_reference"}:
        api = artifact(
            "api_endpoint",
            {
                "method": "GET",
                "path": "/items",
                "auth": "user",
                "request": {},
                "response": {},
                "errors": {},
            },
        )
        if scenario == "unknown_data_entity_reference":
            api["payload"]["data_entities"] = ["missing-entity"]
            component = artifact(
                "component", {"name": "C", "responsibility": "R", "interfaces": []}
            )
            edge(component["id"], api["id"], "calls")
    elif scenario == "screen_missing_states":
        artifact("screen", {"states": ["empty"]})
    elif scenario == "navigation_target_missing":
        screen = artifact("screen")
        edge(screen["id"], "art_01JG7Z3M8Q9XR4T2V6B0N5K1D9", "navigates_to")
    elif scenario == "unmapped_user_flow_step":
        artifact("user_flow", {"name": "Flow", "steps": [{"label": "No map"}]})
    elif scenario == "critical_risk_incomplete":
        artifact(
            "risk",
            {
                "statement": "Risk",
                "probability": "high",
                "impact": "high",
                "mitigation": "",
                "owner": "",
                "severity": "critical",
                "review_date": "",
            },
        )
    elif scenario == "research_claim_without_source":
        artifact("claim", {"statement": "Claim", "evidence_state": "research_backed"})
    elif scenario == "superseding_decision_without_reason":
        artifact(
            "decision",
            {
                "chosen_option": "A",
                "alternatives": [],
                "rationale": "R",
                "consequences": [],
                "supersedes_previous": True,
            },
        )
    elif scenario == "prompt_without_contract_or_eval":
        artifact(
            "prompt",
            {"name": "P", "blocks": [], "output_contract": None, "evaluation_case_ids": []},
        )
    elif scenario == "secret_variable_literal":
        artifact(
            "prompt_variable",
            {
                "name": "TOKEN",
                "type": "string",
                "secret": True,
                "value": "literal-token",
                "secret_ref": None,
            },
        )
    elif scenario == "invalid_skill_frontmatter":
        artifact(
            "skill",
            {
                "name": "skill",
                "version": "1.0.0",
                "content_hash": "hash",
                "trust": "user",
                "directory_name": "skill",
                "frontmatter": {"name": "wrong", "description": "", "allowed_tools": ["admin"]},
                "granted_tools": ["read"],
            },
        )
    elif scenario == "secret_pattern_in_text":
        record = artifact("idea", {"content": "A thought"})
        record["body"] = "password=ThisLooksLikeSecret123"
    elif scenario == "diagram_graph_drift":
        artifact("idea", {"content": "Idea"})
        diagram_source_edges = [{"source_id": "x", "target_id": "y", "edge_type": "contains"}]
    elif scenario == "semantic_hash_mismatch":
        record = artifact("idea", {"content": "Idea"})
        projections = [
            {
                "artifact_id": record["id"],
                "semantic_fields": {"title": "Idea"},
                "semantic_hash": "wrong",
            }
        ]
    elif scenario == "task_without_deliverable":
        artifact("task", {"title": "Task", "acceptance_criteria": [], "depends_on": []})
    elif scenario == "unrecorded_export_revision":
        artifact("idea", {"content": "Idea"})
        project_revisions = [1]
        export_target_revision = 42
    else:
        raise AssertionError(f"Unknown validation fixture: {scenario}")

    return ValidationContext(
        project_id=project_id,
        project_revision=1,
        artifacts=artifacts,
        edges=edges,
        project_revisions=project_revisions,
        export_target_revision=export_target_revision,
        diagram_source_edges=diagram_source_edges,
        projections=projections,
    )


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["rule_id"])
def test_each_validation_rule_has_a_triggering_fixture(case: dict[str, str]) -> None:
    report = validate_project(case_context(case["scenario"]))

    assert any(issue.rule_id == case["rule_id"] for issue in report.issues)
