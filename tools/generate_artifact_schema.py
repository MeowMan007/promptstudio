"""Generate the canonical Artifact JSON Schema from the API's Pydantic model."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any, cast

from prompt_studio_api.contracts.artifact import Artifact

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "artifact.schema.json"
SCHEMA_URL = "https://json-schema.org/draft/2020-12/schema"
SCHEMA_ID = "https://promptstudio.app/schemas/artifact.schema.json"
PAYLOAD_SCHEMAS_PATH = ROOT / "schemas" / "payloads" / "1.0.0.json"


def _inline_refs(value: Any, definitions: dict[str, Any]) -> Any:
    if isinstance(value, list):
        return [_inline_refs(item, definitions) for item in value]
    if not isinstance(value, dict):
        return value

    result = dict(value)
    reference = result.pop("$ref", None)
    if reference is not None:
        name = reference.rsplit("/", 1)[-1]
        resolved = _inline_refs(copy.deepcopy(definitions[name]), definitions)
        result = {**resolved, **result}

    result = {key: _inline_refs(item, definitions) for key, item in result.items()}
    return result


def _normalize(value: Any, *, root: bool = False) -> Any:
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    if not isinstance(value, dict):
        return value

    result = {
        key: (
            {name: _normalize(schema) for name, schema in item.items()}
            if key == "properties" and isinstance(item, dict)
            else _normalize(item)
        )
        for key, item in value.items()
    }
    if not root:
        result.pop("title", None)
    if result.get("default") is None:
        result.pop("default", None)
    if result.get("additionalProperties") in (True, {}):
        result.pop("additionalProperties", None)

    branches = result.get("anyOf")
    if branches and len(branches) == 2:
        nullable = next((branch for branch in branches if branch == {"type": "null"}), None)
        concrete = next((branch for branch in branches if branch is not nullable), None)
        if nullable is not None and concrete is not None and isinstance(concrete.get("type"), str):
            result.pop("anyOf")
            result.update(concrete)
            result["type"] = [concrete["type"], "null"]

    return result


def generated_schema() -> dict[str, Any]:
    raw = Artifact.model_json_schema()
    definitions = raw.pop("$defs", {})
    schema = cast(dict[str, Any], _normalize(_inline_refs(raw, definitions), root=True))
    schema["$schema"] = SCHEMA_URL
    schema["$id"] = SCHEMA_ID
    payload_registry = json.loads(PAYLOAD_SCHEMAS_PATH.read_text(encoding="utf-8"))
    schema["allOf"] = [
        {
            "if": {"properties": {"type": {"const": artifact_type}}, "required": ["type"]},
            "then": {"properties": {"payload": payload_schema}},
        }
        for artifact_type, payload_schema in payload_registry["payload_schemas"].items()
    ]
    return schema


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    encoded = json.dumps(generated_schema(), indent=2, ensure_ascii=False) + "\n"

    if args.check:
        if not SCHEMA_PATH.exists() or SCHEMA_PATH.read_text(encoding="utf-8") != encoded:
            message = f"{SCHEMA_PATH.relative_to(ROOT)} is out of date; run make generate-contracts"
            print(message, file=sys.stderr)
            return 1
        print("Pydantic and JSON Schema agree.")
        return 0

    SCHEMA_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCHEMA_PATH.write_text(encoded, encoding="utf-8")
    print(f"Wrote {SCHEMA_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
