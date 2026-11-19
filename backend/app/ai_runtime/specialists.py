"""
TSK-058: Specialist workflows — discovery, requirements, critic.

Three specialist agents, each scoped to a specific role:
  - DiscoverySpecialist: explores the project graph, produces typed artifact stubs
  - RequirementsSpecialist: refines user stories and requirements
  - CriticSpecialist: reviews proposals, returns structured critique (read-only)

Invariants (TSK-058 acceptance):
  - Each returns typed artifacts only (typed SpecialistResult).
  - CriticSpecialist.review() CANNOT mutate; it returns ReviewReport only.
  - Each has bounded execution (max_steps).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Shared types
# ---------------------------------------------------------------------------

class SpecialistKind(str, Enum):
    DISCOVERY    = "discovery"
    REQUIREMENTS = "requirements"
    CRITIC       = "critic"


@dataclass
class ArtifactStub:
    """A typed artifact produced or proposed by a specialist."""
    artifact_type: str
    title: str
    body: str
    payload: dict[str, Any] = field(default_factory=dict)
    source_specialist: str = ""
    confidence: float = 1.0     # 0.0–1.0


@dataclass
class SpecialistResult:
    """
    Return type for discovery and requirements specialists.
    Contains only typed artifacts — never raw model text.
    """
    specialist: SpecialistKind
    run_id: str
    artifacts: list[ArtifactStub]
    steps_taken: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CriticAnnotation:
    """One annotation from the critic on a specific field/artifact."""
    artifact_type: str
    field_path: str
    severity: str         # "error" | "warning" | "suggestion"
    message: str
    suggestion: str = ""


@dataclass
class ReviewReport:
    """
    Return type for CriticSpecialist — read-only analysis.
    The critic NEVER produces patches or mutations.
    """
    run_id: str
    target_artifact_type: str
    target_field_path: str
    annotations: list[CriticAnnotation]
    overall_score: float          # 0.0–1.0 (1.0 = no issues)
    approved: bool                # True if score >= threshold and no errors
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Discovery specialist
# ---------------------------------------------------------------------------

class DiscoverySpecialist:
    """
    Explores the project context and proposes artifact stubs to create.
    Bounded by max_steps to prevent runaway exploration.
    """

    KIND = SpecialistKind.DISCOVERY

    def __init__(self, max_steps: int = 10) -> None:
        self.max_steps = max_steps

    def run(
        self,
        *,
        run_id: str,
        project_summary: str,
        existing_types: list[str] | None = None,
        hint: str = "",
    ) -> SpecialistResult:
        """
        Discover what artifacts should be created based on project context.
        Returns only typed artifact stubs — never raw text.
        """
        existing = set(existing_types or [])
        stubs: list[ArtifactStub] = []
        steps = 0

        # Heuristic discovery: suggest standard artifact types if missing
        standard_types = [
            ("brief", "Project Brief", "High-level overview of the project."),
            ("persona", "Primary Persona", "The main user of the system."),
            ("user_story", "Core User Story", "A key user need as a user story."),
            ("requirement", "Core Requirement", "A foundational system requirement."),
        ]
        for atype, title, body in standard_types:
            if steps >= self.max_steps:
                break
            if atype not in existing:
                stubs.append(ArtifactStub(
                    artifact_type=atype,
                    title=title,
                    body=body,
                    source_specialist=self.KIND,
                    confidence=0.8,
                ))
            steps += 1

        # If a hint is provided, add a targeted stub
        if hint and steps < self.max_steps:
            stubs.append(ArtifactStub(
                artifact_type="question",
                title=f"Discovery: {hint[:60]}",
                body=f"[Discovery hint] {hint}",
                source_specialist=self.KIND,
                confidence=0.6,
            ))
            steps += 1

        return SpecialistResult(
            specialist=self.KIND,
            run_id=run_id,
            artifacts=stubs,
            steps_taken=steps,
            metadata={"project_summary_len": len(project_summary)},
        )


# ---------------------------------------------------------------------------
# Requirements specialist
# ---------------------------------------------------------------------------

class RequirementsSpecialist:
    """
    Refines user stories and produces structured requirements.
    Takes raw user intent and returns typed requirement/user_story stubs.
    """

    KIND = SpecialistKind.REQUIREMENTS

    def __init__(self, max_steps: int = 10) -> None:
        self.max_steps = max_steps

    def run(
        self,
        *,
        run_id: str,
        user_intent: str,
        artifact_type: str = "user_story",
        persona_name: str = "user",
    ) -> SpecialistResult:
        """
        Refine user intent into typed requirement or user story stubs.
        """
        stubs: list[ArtifactStub] = []
        steps = 0

        # Generate user story
        if artifact_type in ("user_story", "requirement") and steps < self.max_steps:
            story_body = (
                f"As a {persona_name}, I want to {user_intent.strip().rstrip('.')} "
                f"so that I can achieve my goal."
            )
            stubs.append(ArtifactStub(
                artifact_type="user_story",
                title=f"Story: {user_intent[:50]}",
                body=story_body,
                payload={"acceptance_criteria": [
                    f"Given I am a {persona_name}, when I {user_intent[:30]}, then the system responds correctly.",
                ]},
                source_specialist=self.KIND,
                confidence=0.85,
            ))
            steps += 1

        # Derive a requirement from the story
        if steps < self.max_steps:
            stubs.append(ArtifactStub(
                artifact_type="requirement",
                title=f"Req: {user_intent[:50]}",
                body=f"The system shall enable {persona_name} to {user_intent.strip().rstrip('.')}.",
                source_specialist=self.KIND,
                confidence=0.75,
            ))
            steps += 1

        return SpecialistResult(
            specialist=self.KIND,
            run_id=run_id,
            artifacts=stubs,
            steps_taken=steps,
            metadata={"artifact_type": artifact_type, "persona": persona_name},
        )


# ---------------------------------------------------------------------------
# Critic specialist (READ-ONLY)
# ---------------------------------------------------------------------------

class CriticSpecialist:
    """
    Reviews a proposal and returns a structured ReviewReport.
    CANNOT produce patches or mutations of any kind.
    """

    KIND = SpecialistKind.CRITIC
    _APPROVE_THRESHOLD = 0.7

    def review(
        self,
        *,
        run_id: str,
        artifact_type: str,
        field_path: str,
        proposed_value: Any,
        schema: dict[str, Any] | None = None,
        required_fields: list[str] | None = None,
    ) -> ReviewReport:
        """
        Review a proposal.  Returns ReviewReport — NEVER mutates anything.
        """
        annotations: list[CriticAnnotation] = []
        schema = schema or {}
        required_fields = required_fields or []

        # Check type
        expected_type = schema.get("type")
        if expected_type == "string" and not isinstance(proposed_value, str):
            annotations.append(CriticAnnotation(
                artifact_type=artifact_type,
                field_path=field_path,
                severity="error",
                message=f"Expected string, got {type(proposed_value).__name__}",
            ))
        elif expected_type == "array" and not isinstance(proposed_value, list):
            annotations.append(CriticAnnotation(
                artifact_type=artifact_type,
                field_path=field_path,
                severity="error",
                message=f"Expected array, got {type(proposed_value).__name__}",
            ))

        # Check required fields (for dict proposals)
        if isinstance(proposed_value, dict):
            for req in required_fields:
                if req not in proposed_value:
                    annotations.append(CriticAnnotation(
                        artifact_type=artifact_type,
                        field_path=field_path,
                        severity="error",
                        message=f"Required field missing: {req!r}",
                        suggestion=f"Add {req!r} to the proposal.",
                    ))

        # Check string length heuristics
        min_length = schema.get("minLength", 0)
        if isinstance(proposed_value, str) and len(proposed_value) < max(min_length, 10):
            annotations.append(CriticAnnotation(
                artifact_type=artifact_type,
                field_path=field_path,
                severity="warning",
                message=f"Proposal is very short ({len(proposed_value)} chars)",
                suggestion="Expand the proposal with more detail.",
            ))

        error_count = sum(1 for a in annotations if a.severity == "error")
        warning_count = sum(1 for a in annotations if a.severity == "warning")

        score = max(0.0, 1.0 - (error_count * 0.3) - (warning_count * 0.1))
        approved = score >= self._APPROVE_THRESHOLD and error_count == 0

        return ReviewReport(
            run_id=run_id,
            target_artifact_type=artifact_type,
            target_field_path=field_path,
            annotations=annotations,
            overall_score=round(score, 2),
            approved=approved,
        )
