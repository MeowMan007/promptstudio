"""Generate versioned payload schemas from the normative type registry."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
TYPE_REGISTRY_PATH = ROOT / "machine" / "type-registry.json"
OUTPUT_PATH = ROOT / "schemas" / "payloads" / "1.0.0.json"
SCHEMA_URI = "https://json-schema.org/draft/2020-12/schema"

REQUIREMENT_SCHEMA: dict[str, Any] = {
    "$schema": SCHEMA_URI,
    "$id": "https://promptstudio.app/schemas/payloads/1.0.0/requirement.json",
    "type": "object",
    "required": ["ears_pattern", "clauses", "priority", "acceptance_criteria"],
    "additionalProperties": False,
    "properties": {
        "ears_pattern": {
            "enum": [
                "ubiquitous",
                "event_driven",
                "state_driven",
                "unwanted_behaviour",
                "optional_feature",
            ]
        },
        "clauses": {
            "type": "object",
            "required": ["response"],
            "properties": {
                "trigger": {"type": "string"},
                "state": {"type": "string"},
                "condition": {"type": "string"},
                "feature": {"type": "string"},
                "system": {"type": "string"},
                "response": {"type": "string", "minLength": 5},
            },
        },
        "priority": {"enum": ["must", "should", "could", "wont"]},
        "rationale": {"type": "string"},
        "acceptance_criteria": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "given", "when", "then"],
                "additionalProperties": False,
                "properties": {
                    "id": {"type": "string"},
                    "given": {"type": "string"},
                    "when": {"type": "string"},
                    "then": {"type": "string"},
                    "measurable_bound": {"type": ["string", "null"]},
                },
            },
        },
        "exclusions": {"type": "array", "items": {"type": "string"}},
        "waiver": {
            "type": ["object", "null"],
            "properties": {"reason": {"type": "string"}, "approver": {"type": "string"}},
        },
    },
}


def generated_payload_schemas() -> dict[str, Any]:
    registry = json.loads(TYPE_REGISTRY_PATH.read_text(encoding="utf-8"))
    payload_schemas: dict[str, Any] = {}
    for artifact_type, definition in registry["types"].items():
        required = definition["required"]
        schema: dict[str, Any] = {
            "$schema": SCHEMA_URI,
            "$id": f"https://promptstudio.app/schemas/payloads/1.0.0/{artifact_type}.json",
            "title": f"{artifact_type} payload",
            "type": "object",
            "required": required,
            "properties": {field: {} for field in required},
        }
        if artifact_type == "requirement":
            schema = REQUIREMENT_SCHEMA
        elif artifact_type == "screen":
            schema["properties"] = {
                "name": {"type": "string"},
                "route": {"type": "string", "pattern": "^/"},
                "purpose": {"type": "string"},
                "viewport": {
                    "type": "object",
                    "properties": {
                        "preset": {"enum": ["desktop", "tablet", "mobile"]},
                        "w": {"type": "integer"},
                        "h": {"type": "integer"},
                    },
                },
                "regions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["id", "elements"],
                        "properties": {
                            "id": {"type": "string"},
                            "elements": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                },
                "elements": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["id", "component"],
                        "properties": {
                            "id": {"type": "string"},
                            "component": {"type": "string"},
                            "label": {"type": "string"},
                            "required": {"type": "boolean"},
                            "action": {"type": "string"},
                            "validation": {"type": "object"},
                        },
                    },
                },
                "interactions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["id", "trigger", "target", "effect"],
                        "properties": {
                            "id": {"type": "string"},
                            "trigger": {
                                "enum": [
                                    "click",
                                    "submit",
                                    "change",
                                    "blur",
                                    "key",
                                    "route",
                                    "async_done",
                                ]
                            },
                            "target": {"type": "string"},
                            "effect": {"type": "string"},
                            "on_success": {"type": "object"},
                            "on_error": {"type": "object"},
                        },
                    },
                },
                "states": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "enum": [
                            "empty",
                            "loading",
                            "populated",
                            "editing",
                            "invalid",
                            "saving",
                            "saved",
                            "error",
                            "permission_denied",
                            "offline",
                            "success",
                        ]
                    },
                },
                "responsive": {"type": "object"},
                "implements": {"type": "array", "items": {"type": "string"}},
            }
        payload_schemas[artifact_type] = schema

    result = {
        "$schema": SCHEMA_URI,
        "$id": "https://promptstudio.app/schemas/payloads/1.0.0.json",
        "schema_version": "1.0.0",
        "payload_schemas": payload_schemas,
    }
    for schema in payload_schemas.values():
        Draft202012Validator.check_schema(schema)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    encoded = json.dumps(generated_payload_schemas(), indent=2, ensure_ascii=False) + "\n"
    if args.check:
        if not OUTPUT_PATH.exists() or OUTPUT_PATH.read_text(encoding="utf-8") != encoded:
            print(
                "schemas/payloads/1.0.0.json is out of date; run make generate-contracts",
                file=sys.stderr,
            )
            return 1
        print("Payload schemas match the versioned type registry.")
        return 0
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(encoded, encoding="utf-8")
    print("Wrote schemas/payloads/1.0.0.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
