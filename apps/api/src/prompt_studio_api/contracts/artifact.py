from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal, cast

from jsonschema import Draft202012Validator
from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

from prompt_studio_api.contracts.registry import load_payload_schemas, load_type_registry


class ArtifactStatus(StrEnum):
    SCRATCH = "scratch"
    PROPOSED = "proposed"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class Sensitivity(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    SECRET_BEARING = "secret-bearing"


class ProvenanceOrigin(StrEnum):
    USER_INPUT = "user_input"
    PROMPT_RUN = "prompt_run"
    IMPORT = "import"
    SYSTEM = "system"
    INTEGRATION = "integration"


class Provenance(BaseModel):
    origin: ProvenanceOrigin
    run_id: str | None = None
    prompt_version: str | None = None
    skill_version: str | None = None
    model: str | None = None
    input_artifact_ids: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0, le=1)


class Artifact(BaseModel):
    model_config = ConfigDict(extra="forbid", title="Artifact")

    id: str = Field(pattern=r"^art_[0-9A-HJKMNP-TV-Z]{26}$")
    alias: str = Field(pattern=r"^[A-Z]{3}-[0-9]{3,6}$")
    project_id: str = Field(pattern=r"^prj_[0-9A-HJKMNP-TV-Z]{26}$")
    type: str = Field(
        description="Closed artifact type from machine/type-registry.json",
        json_schema_extra=cast(Any, {"enum": sorted(load_type_registry().types)}),
    )
    schema_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(default_factory=str)
    payload: dict[str, Any]
    status: ArtifactStatus
    revision: int = Field(ge=1)
    created_by: str
    updated_by: str
    visibility: Literal["project", "private", "restricted"] = "project"
    owner: str | None = None
    tags: list[str] = Field(
        default_factory=list,
        json_schema_extra={"uniqueItems": True},
    )
    sensitivity: Sensitivity = Sensitivity.INTERNAL
    locked_fields: list[str] = Field(default_factory=list)
    provenance: Provenance
    created_at: datetime
    updated_at: datetime

    @field_validator("tags")
    @classmethod
    def tags_are_unique(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("tags must be unique")
        return values

    @field_validator("type")
    @classmethod
    def type_is_registered(cls, value: str) -> str:
        if value not in load_type_registry().types:
            raise ValueError("unknown artifact type")
        return value

    @field_validator("payload")
    @classmethod
    def payload_matches_type_schema(
        cls, value: dict[str, Any], info: ValidationInfo
    ) -> dict[str, Any]:
        artifact_type = info.data.get("type")
        schema_version = info.data.get("schema_version")
        if not isinstance(artifact_type, str) or not isinstance(schema_version, str):
            return value
        try:
            schemas = load_payload_schemas(schema_version)
        except RuntimeError as exc:
            raise ValueError(str(exc)) from exc
        schema = schemas.get(artifact_type)
        if schema is None:
            raise ValueError(
                f"No payload schema for type {artifact_type} at version {schema_version}"
            )
        errors = sorted(
            Draft202012Validator(schema).iter_errors(value),
            key=lambda error: tuple(str(part) for part in error.absolute_path),
        )
        if errors:
            messages = [
                (
                    f"payload/{'/'.join(str(part) for part in error.absolute_path) or '$'}: "
                    f"{error.message}"
                )
                for error in errors
            ]
            raise ValueError("; ".join(messages))
        return value
