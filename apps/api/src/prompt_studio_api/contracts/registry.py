from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

RegistryFamily = Literal[
    "thinking",
    "product",
    "decision",
    "ux",
    "design",
    "engineering",
    "prompting",
    "quality",
    "delivery",
    "evidence",
]
REGISTRY_ROOT = Path(__file__).resolve().parents[5] / "machine"


class TypeDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")
    family: RegistryFamily
    required: list[str]
    promptable: list[str]


class TypeRegistry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    registry_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    types: dict[str, TypeDefinition]

    @model_validator(mode="after")
    def validate_types(self) -> TypeRegistry:
        if not self.types:
            raise ValueError("type registry cannot be empty")
        for name in self.types:
            if not re.fullmatch(r"[a-z][a-z0-9_]*", name):
                raise ValueError(f"invalid artifact type name: {name}")
        return self


class EdgeDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    sources: list[str] | None = Field(default=None, alias="from")
    targets: list[str] | None = Field(default=None, alias="to")
    derived_inverse_of: str | None = None
    acyclic: bool = False
    creates_issue: bool = False
    requires_reason: bool = False
    excluded_from_coverage: bool = False
    warning: bool = False

    @model_validator(mode="after")
    def validate_direction(self) -> EdgeDefinition:
        if self.derived_inverse_of is None and (self.sources is None or self.targets is None):
            raise ValueError("stored edge types must declare from and to endpoint lists")
        if self.derived_inverse_of is not None and (
            self.sources is not None or self.targets is not None
        ):
            raise ValueError("derived inverse edges cannot declare stored endpoints")
        return self


class EdgeRegistry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    registry_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    edges: dict[str, EdgeDefinition]

    @model_validator(mode="after")
    def validate_edges(self) -> EdgeRegistry:
        if not self.edges:
            raise ValueError("edge registry cannot be empty")
        for name in self.edges:
            if not re.fullmatch(r"[a-z][a-z0-9_]*", name):
                raise ValueError(f"invalid edge type name: {name}")
        for name, edge in self.edges.items():
            if edge.derived_inverse_of is not None and edge.derived_inverse_of not in self.edges:
                raise ValueError(f"{name} refers to an unknown inverse edge")
        return self


def _read_registry(path: Path) -> dict[str, Any]:
    try:
        content = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not load registry at {path}") from exc
    if not isinstance(content, dict):
        raise RuntimeError(f"Registry at {path} must contain a JSON object")
    return content


@lru_cache(maxsize=1)
def load_type_registry() -> TypeRegistry:
    return TypeRegistry.model_validate(_read_registry(REGISTRY_ROOT / "type-registry.json"))


@lru_cache(maxsize=1)
def load_edge_registry() -> EdgeRegistry:
    return EdgeRegistry.model_validate(_read_registry(REGISTRY_ROOT / "edge-registry.json"))


def load_payload_schemas(schema_version: str) -> dict[str, dict[str, Any]]:
    path = REGISTRY_ROOT.parent / "schemas" / "payloads" / f"{schema_version}.json"
    content = _read_registry(path)
    if content.get("schema_version") != schema_version:
        raise RuntimeError(f"Payload schema version mismatch in {path}")
    payload_schemas = content.get("payload_schemas")
    if not isinstance(payload_schemas, dict):
        raise RuntimeError(f"Payload schemas are malformed in {path}")
    return payload_schemas


def validate_edge_pair(edge_type: str, source_type: str, target_type: str) -> EdgeDefinition:
    definition = load_edge_registry().edges.get(edge_type)
    if definition is None:
        raise ValueError(f"Unknown edge type: {edge_type}")
    if definition.derived_inverse_of is not None:
        raise ValueError(f"Edge type {edge_type} is derived and cannot be stored")
    if definition.sources is None or definition.targets is None:
        raise ValueError(f"Edge type {edge_type} has no stored direction")
    if "*" not in definition.sources and source_type not in definition.sources:
        raise ValueError(f"Source type {source_type} is not allowed for {edge_type}")
    if "*" not in definition.targets and target_type not in definition.targets:
        raise ValueError(f"Target type {target_type} is not allowed for {edge_type}")
    return definition
