from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from prompt_studio_api.contracts.artifact import Artifact
from prompt_studio_api.contracts.registry import load_edge_registry, load_type_registry
from pydantic import ValidationError

from backend.app.ids import alias_prefix_for_type, new_artifact_id, new_export_id, new_ulid

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads((ROOT / "schemas" / "artifact.schema.json").read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA)


def valid_artifact() -> dict[str, object]:
    now = datetime.now(UTC).isoformat()
    return {
        "id": "art_01JG7Z3M8Q9XR4T2V6B0N5K1D9",
        "alias": "REQ-001",
        "project_id": "prj_01JG7Z3M8Q9XR4T2V6B0N5K1DB",
        "type": "requirement",
        "schema_version": "1.0.0",
        "title": "Workspace scaffold",
        "payload": {
            "ears_pattern": "ubiquitous",
            "clauses": {"response": "The system shall preserve the project."},
            "priority": "must",
            "acceptance_criteria": [],
        },
        "status": "proposed",
        "revision": 1,
        "created_by": "user-123",
        "updated_by": "user-123",
        "provenance": {"origin": "user_input"},
        "created_at": now,
        "updated_at": now,
    }


def test_artifact_passes_pydantic_and_json_schema() -> None:
    artifact = Artifact.model_validate(valid_artifact())
    VALIDATOR.validate(artifact.model_dump(mode="json"))


def test_invalid_artifact_is_rejected_by_both_contracts() -> None:
    invalid = valid_artifact()
    invalid["title"] = ""

    with pytest.raises(ValidationError):
        Artifact.model_validate(invalid)
    assert list(VALIDATOR.iter_errors(invalid))


def test_duplicate_tags_are_rejected_by_both_contracts() -> None:
    invalid = valid_artifact()
    invalid["tags"] = ["priority", "priority"]

    with pytest.raises(ValidationError):
        Artifact.model_validate(invalid)
    assert list(VALIDATOR.iter_errors(invalid))


def test_registry_type_is_closed_in_pydantic_and_json_schema() -> None:
    invalid = valid_artifact()
    invalid["type"] = "invented_type"

    with pytest.raises(ValidationError, match="unknown artifact type"):
        Artifact.model_validate(invalid)
    assert list(VALIDATOR.iter_errors(invalid))


def test_normative_registries_load_and_validate() -> None:
    types = load_type_registry()
    edges = load_edge_registry()

    assert types.registry_version == "1.0.0"
    assert len(types.types) >= 40
    assert types.types["requirement"].family == "product"
    assert edges.registry_version == "1.0.0"
    assert edges.edges["depends_on"].acyclic is True
    assert edges.edges["realized_by"].derived_inverse_of == "implements"
    prefixes = [alias_prefix_for_type(artifact_type) for artifact_type in types.types]
    assert len(prefixes) == len(set(prefixes))
    assert new_artifact_id().startswith("art_")
    assert new_export_id().startswith("exp_")
    assert len(new_ulid()) == 26


def test_every_registered_artifact_type_accepts_its_required_payload() -> None:
    registry = load_type_registry()
    for artifact_type, definition in registry.types.items():
        payload: dict[str, object] = {field: "value" for field in definition.required}
        if artifact_type == "requirement":
            payload = {
                "ears_pattern": "ubiquitous",
                "clauses": {"response": "System responds successfully."},
                "priority": "should",
                "acceptance_criteria": [],
            }
        elif artifact_type == "screen":
            payload.update(
                {
                    "route": "/settings",
                    "regions": [],
                    "elements": [],
                    "states": ["empty"],
                }
            )
        data = valid_artifact()
        data["type"] = artifact_type
        data["payload"] = payload
        Artifact.model_validate(data)


def test_type_specific_payload_errors_name_invalid_fields() -> None:
    invalid_payloads = [
        ({"ears_pattern": "invented"}, "ears_pattern"),
        ({"priority": "urgent"}, "priority"),
        ({"clauses": {"response": "bad"}}, "clauses/response"),
        (
            {
                "acceptance_criteria": [
                    {
                        "id": "AC-1",
                        "given": "known",
                        "when": "saved",
                        "then": "works",
                        "extra": True,
                    }
                ]
            },
            "acceptance_criteria/0",
        ),
    ]
    for change, expected_path in invalid_payloads:
        invalid = valid_artifact()
        payload = dict(invalid["payload"])
        payload.update(change)
        invalid["payload"] = payload
        with pytest.raises(ValidationError) as error:
            Artifact.model_validate(invalid)
        assert expected_path in str(error.value)


def test_unsupported_payload_schema_version_is_rejected() -> None:
    invalid = valid_artifact()
    invalid["schema_version"] = "9.9.9"

    with pytest.raises(ValidationError, match="Could not load registry"):
        Artifact.model_validate(invalid)
