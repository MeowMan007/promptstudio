"""TSK-096: OpenAPI 3.1 generator + validator gate.

Implements spec section 25.2:
  - generate_openapi(): produces OpenAPI 3.1 JSON/YAML from api_endpoint artifacts
  - x-todo extension for incomplete endpoints
  - validate_openapi(): validates against OAS 3.1 meta-schema subset
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

class HTTPMethod(str, Enum):
    GET = "get"
    POST = "post"
    PUT = "put"
    PATCH = "patch"
    DELETE = "delete"
    OPTIONS = "options"
    HEAD = "head"


@dataclass
class APIParameter:
    name: str
    location: str   # "path" | "query" | "header" | "cookie"
    required: bool = False
    description: str = ""
    schema: dict[str, Any] = field(default_factory=lambda: {"type": "string"})


@dataclass
class APIResponse:
    status_code: str    # "200", "201", "400", "default", etc.
    description: str
    schema: dict[str, Any] | None = None
    content_type: str = "application/json"


@dataclass
class APIEndpoint:
    path: str           # e.g. "/projects/{project_id}"
    method: HTTPMethod
    operation_id: str
    summary: str = ""
    description: str = ""
    tags: list[str] = field(default_factory=list)
    parameters: list[APIParameter] = field(default_factory=list)
    request_body_schema: dict[str, Any] | None = None
    responses: list[APIResponse] = field(default_factory=list)
    is_complete: bool = True    # False → x-todo added
    todo_note: str = ""


@dataclass
class APIInfo:
    title: str
    version: str = "0.1.0"
    description: str = ""
    contact_email: str = ""
    license_name: str = "MIT"
    servers: list[str] = field(default_factory=lambda: ["http://localhost:8000"])


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

def _build_operation(endpoint: APIEndpoint) -> dict[str, Any]:
    op: dict[str, Any] = {
        "operationId": endpoint.operation_id,
        "summary": endpoint.summary or endpoint.operation_id,
        "tags": endpoint.tags or ["default"],
    }
    if endpoint.description:
        op["description"] = endpoint.description
    if not endpoint.is_complete:
        op["x-todo"] = endpoint.todo_note or "Implementation pending"

    # Parameters
    if endpoint.parameters:
        op["parameters"] = [
            {
                "name": p.name,
                "in": p.location,
                "required": p.required,
                "description": p.description,
                "schema": p.schema,
            }
            for p in endpoint.parameters
        ]

    # Request body
    if endpoint.request_body_schema is not None:
        op["requestBody"] = {
            "required": True,
            "content": {
                "application/json": {"schema": endpoint.request_body_schema}
            },
        }

    # Responses
    if endpoint.responses:
        op["responses"] = {
            r.status_code: {
                "description": r.description,
                **(
                    {"content": {r.content_type: {"schema": r.schema}}}
                    if r.schema else {}
                ),
            }
            for r in endpoint.responses
        }
    else:
        op["responses"] = {"200": {"description": "Success"}}

    return op


def generate_openapi(
    info: APIInfo,
    endpoints: list[APIEndpoint],
    components: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate an OpenAPI 3.1 document as a Python dict.

    Incomplete endpoints get an ``x-todo`` extension field.
    The document is deterministic: endpoints are sorted by (path, method).
    """
    paths: dict[str, dict[str, Any]] = {}

    sorted_endpoints = sorted(endpoints, key=lambda e: (e.path, e.method.value))
    for ep in sorted_endpoints:
        if ep.path not in paths:
            paths[ep.path] = {}
        paths[ep.path][ep.method.value] = _build_operation(ep)

    doc: dict[str, Any] = {
        "openapi": "3.1.0",
        "info": {
            "title": info.title,
            "version": info.version,
            "description": info.description,
            **({"contact": {"email": info.contact_email}} if info.contact_email else {}),
            "license": {"name": info.license_name},
        },
        "servers": [{"url": s} for s in info.servers],
        "paths": paths,
    }
    if components:
        doc["components"] = components

    return doc


def openapi_to_json(doc: dict[str, Any], indent: int = 2) -> str:
    """Serialize OpenAPI dict to deterministic JSON string."""
    return json.dumps(doc, sort_keys=True, indent=indent)


# ---------------------------------------------------------------------------
# Validator gate (spec 25.2 — "parses with 3.1 validator")
# ---------------------------------------------------------------------------

class OpenAPIValidationError(ValueError):
    pass


_REQUIRED_TOP_LEVEL = {"openapi", "info", "paths"}
_REQUIRED_INFO = {"title", "version"}


def validate_openapi(doc: dict[str, Any]) -> list[str]:
    """Validate an OpenAPI 3.1 document.

    Returns a list of error strings (empty = valid).
    Uses a lightweight structural check covering:
      - Required top-level keys
      - info.title / info.version presence
      - openapi version prefix "3.1."
      - Each path is a string starting with "/"
      - Each operation has an operationId
      - Responses present on each operation
    """
    errors: list[str] = []

    missing = _REQUIRED_TOP_LEVEL - set(doc.keys())
    if missing:
        errors.append(f"Missing top-level keys: {sorted(missing)}")
        return errors  # can't proceed

    version = doc.get("openapi", "")
    if not version.startswith("3.1."):
        errors.append(f"openapi version must start with '3.1.', got: {version!r}")

    info = doc.get("info", {})
    missing_info = _REQUIRED_INFO - set(info.keys())
    if missing_info:
        errors.append(f"info missing keys: {sorted(missing_info)}")

    paths = doc.get("paths", {})
    if not isinstance(paths, dict):
        errors.append("paths must be an object")
        return errors

    for path, path_item in paths.items():
        if not path.startswith("/"):
            errors.append(f"Path must start with '/': {path!r}")
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method.startswith("x-"):
                continue
            if not isinstance(operation, dict):
                continue
            if "operationId" not in operation:
                errors.append(f"Missing operationId: {method.upper()} {path}")
            if "responses" not in operation:
                errors.append(f"Missing responses: {method.upper()} {path}")

    return errors


def assert_valid_openapi(doc: dict[str, Any]) -> None:
    """Raise OpenAPIValidationError if the document is invalid."""
    errors = validate_openapi(doc)
    if errors:
        raise OpenAPIValidationError(
            f"OpenAPI validation failed ({len(errors)} error(s)):\n"
            + "\n".join(f"  • {e}" for e in errors)
        )
