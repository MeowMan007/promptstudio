from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic import ValidationError as PydanticValidationError

from backend.app.graph.edges import creates_cycle
from prompt_studio_api.contracts.artifact import Artifact
from prompt_studio_api.contracts.registry import validate_edge_pair

Severity = Literal["blocker", "warning"]


class ValidationIssue(BaseModel):
    rule_id: str
    severity: Severity
    message: str
    artifact_id: str | None = None
    edge_id: str | None = None


class ValidationContext(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: str
    project_revision: int = 1
    artifacts: list[dict[str, Any]] = Field(default_factory=list)
    edges: list[dict[str, Any]] = Field(default_factory=list)
    project_revisions: list[int] = Field(default_factory=list)
    export_target_revision: int | None = None
    diagram_source_edges: list[dict[str, str]] = Field(default_factory=list)
    projections: list[dict[str, Any]] = Field(default_factory=list)


class ValidationReport(BaseModel):
    project_id: str
    revision: int
    valid: bool
    blockers: int
    warnings: int
    issues: list[ValidationIssue]


SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"(?i)(?:password|api[_-]?key|client[_-]?secret)\s*[:=]\s*['\"]?[^\s'\"]{8,}"),
)


def _text_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [text for child in value.values() for text in _text_values(child)]
    if isinstance(value, list):
        return [text for child in value for text in _text_values(child)]
    return []


def _artifact_snapshot(context: ValidationContext) -> dict[str, dict[str, Any]]:
    return {
        artifact["id"]: artifact
        for artifact in context.artifacts
        if isinstance(artifact.get("id"), str)
    }


def _payload_of(artifact: dict[str, Any]) -> dict[str, Any]:
    payload = artifact.get("payload")
    return payload if isinstance(payload, dict) else {}


def _issue(
    rule_id: str,
    severity: Severity,
    message: str,
    *,
    artifact_id: str | None = None,
    edge_id: str | None = None,
) -> ValidationIssue:
    return ValidationIssue(
        rule_id=rule_id,
        severity=severity,
        message=message,
        artifact_id=artifact_id,
        edge_id=edge_id,
    )


def validate_project(context: ValidationContext) -> ValidationReport:
    issues: list[ValidationIssue] = []
    artifacts = context.artifacts
    by_id = _artifact_snapshot(context)
    edges = context.edges

    # VAL-01: validate the full envelope, including each declared payload schema.
    for raw in artifacts:
        try:
            Artifact.model_validate(raw)
        except (PydanticValidationError, ValueError) as exc:
            issues.append(_issue("VAL-01", "blocker", str(exc), artifact_id=raw.get("id")))

    # VAL-02: unique immutable IDs and project-local aliases.
    seen_ids: set[str] = set()
    seen_aliases: set[str] = set()
    for raw in artifacts:
        artifact_id = raw.get("id")
        alias = raw.get("alias")
        if isinstance(artifact_id, str) and artifact_id in seen_ids:
            issues.append(
                _issue("VAL-02", "blocker", "Duplicate artifact id", artifact_id=artifact_id)
            )
        if isinstance(alias, str) and alias in seen_aliases:
            issues.append(
                _issue("VAL-02", "blocker", "Duplicate project alias", artifact_id=artifact_id)
            )
        if isinstance(artifact_id, str):
            seen_ids.add(artifact_id)
        if isinstance(alias, str):
            seen_aliases.add(alias)

    # VAL-03/04: edge resolution and type-pair registry checks.
    for edge in edges:
        source = by_id.get(str(edge.get("source_id")))
        target = by_id.get(str(edge.get("target_id")))
        edge_id = edge.get("id")
        if source is None or target is None:
            issues.append(
                _issue(
                    "VAL-03",
                    "blocker",
                    "Edge endpoint does not resolve in this project",
                    edge_id=edge_id,
                )
            )
            continue
        if (
            source.get("project_id") != context.project_id
            or target.get("project_id") != context.project_id
        ):
            issues.append(
                _issue(
                    "VAL-03", "blocker", "Edge endpoints must share the project", edge_id=edge_id
                )
            )
            continue
        try:
            validate_edge_pair(
                str(edge.get("edge_type")), str(source.get("type")), str(target.get("type"))
            )
        except ValueError as exc:
            issues.append(_issue("VAL-04", "blocker", str(exc), edge_id=edge_id))

    # VAL-05: directed cycle checks for the two registry subgraphs.
    for edge_type in ("contains", "depends_on"):
        selected = [edge for edge in edges if edge.get("edge_type") == edge_type]
        graph = [(str(edge.get("source_id")), str(edge.get("target_id"))) for edge in selected]
        checked: list[tuple[str, str]] = []
        for edge in selected:
            source_id = str(edge.get("source_id"))
            target_id = str(edge.get("target_id"))
            if creates_cycle(checked, source_id=source_id, target_id=target_id):
                issues.append(
                    _issue(
                        "VAL-05", "blocker", f"Cycle in {edge_type} graph", edge_id=edge.get("id")
                    )
                )
                break
            checked.append((source_id, target_id))
        if not graph:
            continue

    outgoing: dict[str, list[dict[str, Any]]] = {}
    incoming: dict[str, list[dict[str, Any]]] = {}
    for edge in edges:
        outgoing.setdefault(str(edge.get("source_id")), []).append(edge)
        incoming.setdefault(str(edge.get("target_id")), []).append(edge)

    # VAL-06..VAL-19: domain-specific completeness and policy checks.
    for artifact in artifacts:
        artifact_id = str(artifact.get("id", ""))
        artifact_type = artifact.get("type")
        payload = _payload_of(artifact)
        status = artifact.get("status")

        if artifact_type == "requirement" and status == "approved":
            if payload.get("priority") == "must" and not payload.get("acceptance_criteria"):
                issues.append(
                    _issue(
                        "VAL-06",
                        "blocker",
                        "Approved must requirement needs acceptance criteria",
                        artifact_id=artifact_id,
                    )
                )
            validated = any(
                edge.get("edge_type") == "validated_by"
                and edge.get("source_id") == artifact_id
                and (target_record := by_id.get(str(edge.get("target_id")))) is not None
                and target_record.get("type") in {"test_case", "evaluation_case"}
                for edge in outgoing.get(artifact_id, [])
            )
            waiver = payload.get("waiver")
            waived = isinstance(waiver, dict) and bool(waiver.get("reason"))
            if not validated and not waived:
                issues.append(
                    _issue(
                        "VAL-07",
                        "warning",
                        "Approved requirement lacks validation evidence or waiver",
                        artifact_id=artifact_id,
                    )
                )

        if artifact_type == "component":
            implements = any(
                edge.get("edge_type") == "implements" for edge in outgoing.get(artifact_id, [])
            )
            if not implements and not payload.get("platform_purpose"):
                issues.append(
                    _issue(
                        "VAL-08",
                        "warning",
                        "Component needs an implemented requirement or platform_purpose",
                        artifact_id=artifact_id,
                    )
                )

        if artifact_type == "api_endpoint":
            required = ("auth", "request", "response", "errors")
            if any(not payload.get(field) for field in required) or not any(
                edge.get("edge_type") == "calls"
                and (source_record := by_id.get(str(edge.get("source_id")))) is not None
                and source_record.get("type") == "component"
                for edge in incoming.get(artifact_id, [])
            ):
                issues.append(
                    _issue(
                        "VAL-09",
                        "blocker",
                        "API endpoint needs an owner and auth/request/response/error contracts",
                        artifact_id=artifact_id,
                    )
                )
            references = payload.get("data_entities", [])
            if isinstance(references, list) and any(
                reference not in by_id or by_id[reference].get("type") != "data_entity"
                for reference in references
                if isinstance(reference, str)
            ):
                issues.append(
                    _issue(
                        "VAL-10",
                        "warning",
                        "API endpoint references an unknown data entity",
                        artifact_id=artifact_id,
                    )
                )

        if artifact_type == "screen":
            states = payload.get("states", [])
            if not isinstance(states, list) or not {
                "empty",
                "loading",
                "error",
                "success",
            }.issubset(states):
                issues.append(
                    _issue(
                        "VAL-11",
                        "warning",
                        "Screen needs empty, loading, error and success states",
                        artifact_id=artifact_id,
                    )
                )

        if artifact_type == "user_flow":
            steps = payload.get("steps", [])
            if isinstance(steps, list):
                for step in steps:
                    if not isinstance(step, dict):
                        continue
                    references = [step.get("screen_id"), step.get("interaction_id")]
                    if not any(
                        reference in by_id for reference in references if isinstance(reference, str)
                    ) and not step.get("gap"):
                        issues.append(
                            _issue(
                                "VAL-13",
                                "warning",
                                "User-flow step needs a screen, interaction or documented gap",
                                artifact_id=artifact_id,
                            )
                        )
                        break

        if artifact_type == "risk" and str(payload.get("severity", "")).lower() == "critical":
            if (
                not artifact.get("owner")
                and not payload.get("owner")
                or not payload.get("mitigation")
                or not payload.get("review_date")
            ):
                issues.append(
                    _issue(
                        "VAL-14",
                        "blocker",
                        "Critical risk needs an owner, mitigation and review date",
                        artifact_id=artifact_id,
                    )
                )

        if artifact_type == "claim" and payload.get("evidence_state") == "research_backed":
            supported = any(
                edge.get("edge_type") == "supports" for edge in incoming.get(artifact_id, [])
            )
            if not supported:
                issues.append(
                    _issue(
                        "VAL-15",
                        "warning",
                        "Research-backed claim needs a source edge or an assumption label",
                        artifact_id=artifact_id,
                    )
                )

        if artifact_type in {"decision", "adr"} and payload.get("supersedes_previous"):
            supersedes = [
                edge
                for edge in outgoing.get(artifact_id, [])
                if edge.get("edge_type") == "supersedes"
            ]
            if not any(
                isinstance(edge.get("metadata"), dict) and edge["metadata"].get("reason")
                for edge in supersedes
            ):
                issues.append(
                    _issue(
                        "VAL-16",
                        "blocker",
                        "Superseding decision needs a prior-decision edge with reason",
                        artifact_id=artifact_id,
                    )
                )

        if artifact_type == "prompt":
            if not payload.get("output_contract") or not payload.get("evaluation_case_ids"):
                issues.append(
                    _issue(
                        "VAL-17",
                        "warning",
                        "Prompt needs an output contract and evaluation case",
                        artifact_id=artifact_id,
                    )
                )

        if artifact_type == "prompt_variable" and payload.get("secret"):
            secret_ref = payload.get("secret_ref")
            if not isinstance(secret_ref, str) or not secret_ref or payload.get("value"):
                issues.append(
                    _issue(
                        "VAL-18",
                        "blocker",
                        "Secret variable must use a reference and cannot contain a literal",
                        artifact_id=artifact_id,
                    )
                )

        if artifact_type == "skill":
            frontmatter = payload.get("frontmatter")
            granted_tools = payload.get("granted_tools", [])
            if (
                not isinstance(frontmatter, dict)
                or not frontmatter.get("name")
                or not frontmatter.get("description")
                or frontmatter.get("name") != payload.get("directory_name")
                or not isinstance(frontmatter.get("allowed_tools", []), list)
                or not set(frontmatter.get("allowed_tools", [])).issubset(set(granted_tools))
            ):
                issues.append(
                    _issue(
                        "VAL-19",
                        "blocker",
                        "Skill frontmatter, directory name or allowed tools are invalid",
                        artifact_id=artifact_id,
                    )
                )

        if artifact_type == "task" and not payload.get("deliverable_ids"):
            issues.append(
                _issue(
                    "VAL-23",
                    "warning",
                    "Task needs a deliverable artifact",
                    artifact_id=artifact_id,
                )
            )

        if any(
            pattern.search(text)
            for text in [
                str(artifact.get("title", "")),
                str(artifact.get("body", "")),
                *_text_values(payload),
            ]
            for pattern in SECRET_PATTERNS
        ):
            issues.append(
                _issue(
                    "VAL-20",
                    "blocker",
                    "Exportable artifact text contains a secret pattern",
                    artifact_id=artifact_id,
                )
            )

    # VAL-12: navigation edges must resolve even when the overall graph is malformed.
    for edge in edges:
        if edge.get("edge_type") == "navigates_to" and edge.get("target_id") not in by_id:
            issues.append(
                _issue(
                    "VAL-12", "blocker", "Navigation target does not exist", edge_id=edge.get("id")
                )
            )

    # VAL-21/22: canvas and diagram projections must match semantic graph state.
    graph_diagram_edges = sorted(
        (str(edge.get("source_id")), str(edge.get("target_id")), str(edge.get("edge_type")))
        for edge in edges
        if edge.get("edge_type") in {"contains", "navigates_to", "implements", "depends_on"}
    )
    source_diagram_edges = sorted(
        (edge.get("source_id", ""), edge.get("target_id", ""), edge.get("edge_type", ""))
        for edge in context.diagram_source_edges
    )
    if (
        source_diagram_edges
        and source_diagram_edges != graph_diagram_edges
        and not any(
            artifact.get("type") == "issue" and _payload_of(artifact).get("diagram_drift")
            for artifact in artifacts
        )
    ):
        issues.append(
            _issue(
                "VAL-21", "warning", "Diagram source differs from typed graph without a drift issue"
            )
        )
    for projection in context.projections:
        semantic_fields = projection.get("semantic_fields")
        expected_hash = hashlib.sha256(
            json.dumps(semantic_fields, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        expected_hash = f"sha256:{expected_hash}"
        if projection.get("semantic_hash") != expected_hash:
            issues.append(
                _issue(
                    "VAL-22",
                    "blocker",
                    "Layout projection changed or mismatched semantic fields",
                    artifact_id=projection.get("artifact_id"),
                )
            )

    # VAL-24: exported target revisions must be pinned to a known immutable revision.
    if (
        context.export_target_revision is not None
        and context.export_target_revision not in context.project_revisions
    ):
        issues.append(
            _issue(
                "VAL-24", "blocker", "Export target revision is not an immutable recorded revision"
            )
        )

    return ValidationReport(
        project_id=context.project_id,
        revision=context.project_revision,
        valid=not any(issue.severity == "blocker" for issue in issues),
        blockers=sum(issue.severity == "blocker" for issue in issues),
        warnings=sum(issue.severity == "warning" for issue in issues),
        issues=issues,
    )
