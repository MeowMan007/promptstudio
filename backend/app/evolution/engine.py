"""
TSK-074: Progress model computation + snapshots.
TSK-075: Evolution engine — triggers, operators, proposals.
TSK-076: Skill unlock rules + stage rail.

TSK-074 — Progress model:
  Deterministic signals and maturity score. Recomputed after each patch apply.
  A project moves through stages: discovery → ideation → definition → design → delivery.
  Each stage has minimum artifact requirements and quality thresholds.

TSK-075 — Evolution engine:
  Monitors changes (via staleness reports + patch events) and emits reviewable proposals.
  Each trigger has a test; operators emit binding patches (never direct applies).

TSK-076 — Skill unlock rules:
  Skills unlock when stage/progress thresholds are met.
  Suggestions (from the evolution engine) are NEVER auto-run.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# =============================================================================
# TSK-074: Progress model
# =============================================================================

class ProjectStage(str, Enum):
    DISCOVERY  = "discovery"
    IDEATION   = "ideation"
    DEFINITION = "definition"
    DESIGN     = "design"
    DELIVERY   = "delivery"


_STAGE_ORDER = [
    ProjectStage.DISCOVERY,
    ProjectStage.IDEATION,
    ProjectStage.DEFINITION,
    ProjectStage.DESIGN,
    ProjectStage.DELIVERY,
]


@dataclass
class SignalResult:
    """One computed signal."""
    signal_id: str
    name: str
    value: float            # 0.0–1.0
    weight: float = 1.0
    evidence: str = ""


@dataclass
class ProgressSnapshot:
    """
    Deterministic snapshot of project progress.
    Recomputed after each patch apply.
    """
    project_id: str
    stage: ProjectStage
    maturity: float                 # 0.0–1.0, weighted average of signals
    signals: list[SignalResult]
    computed_at: float = field(default_factory=time.monotonic)
    snapshot_hash: str = ""         # sha256 of deterministic serialisation

    @property
    def stage_index(self) -> int:
        return _STAGE_ORDER.index(self.stage)

    def can_advance(self) -> bool:
        """True if maturity is high enough to advance to next stage."""
        return self.maturity >= 0.6 and self.stage != ProjectStage.DELIVERY


# ---------------------------------------------------------------------------
# Signal definitions (deterministic, based on artifact counts + quality)
# ---------------------------------------------------------------------------

@dataclass
class ArtifactSummary:
    """Lightweight snapshot of artifacts in a project for signal computation."""
    type_counts: dict[str, int]       # artifact_type → count
    quality_scores: dict[str, float]  # artifact_type → avg quality (0–1)
    total: int = 0


def compute_progress(
    project_id: str,
    artifacts: ArtifactSummary,
    *,
    current_stage: ProjectStage = ProjectStage.DISCOVERY,
) -> ProgressSnapshot:
    """
    Compute a deterministic ProgressSnapshot from an ArtifactSummary.
    Signals are defined per-stage and weighted.
    """
    import hashlib, json

    signals: list[SignalResult] = []

    # Signal 1: Has brief
    has_brief = min(1.0, artifacts.type_counts.get("brief", 0) / 1.0)
    signals.append(SignalResult("S01", "has_brief", has_brief, weight=2.0,
                                evidence=f"brief count={artifacts.type_counts.get('brief', 0)}"))

    # Signal 2: Has at least one persona
    has_persona = min(1.0, artifacts.type_counts.get("persona", 0) / 1.0)
    signals.append(SignalResult("S02", "has_persona", has_persona, weight=1.5,
                                evidence=f"persona count={artifacts.type_counts.get('persona', 0)}"))

    # Signal 3: Has user stories
    story_count = artifacts.type_counts.get("user_story", 0)
    has_stories = min(1.0, story_count / 3.0)
    signals.append(SignalResult("S03", "has_user_stories", has_stories, weight=2.0,
                                evidence=f"user_story count={story_count}"))

    # Signal 4: Has requirements
    req_count = artifacts.type_counts.get("requirement", 0)
    has_reqs = min(1.0, req_count / 5.0)
    signals.append(SignalResult("S04", "has_requirements", has_reqs, weight=1.5,
                                evidence=f"requirement count={req_count}"))

    # Signal 5: Has decisions / ADRs
    dec_count = artifacts.type_counts.get("decision", 0)
    has_decisions = min(1.0, dec_count / 2.0)
    signals.append(SignalResult("S05", "has_decisions", has_decisions, weight=1.0,
                                evidence=f"decision count={dec_count}"))

    # Signal 6: Quality of stories (from quality_scores)
    story_quality = artifacts.quality_scores.get("user_story", 0.0)
    signals.append(SignalResult("S06", "story_quality", story_quality, weight=1.5,
                                evidence=f"avg quality={story_quality:.2f}"))

    # Signal 7: Has screens / design artifacts
    screen_count = artifacts.type_counts.get("screen", 0)
    has_design = min(1.0, screen_count / 2.0)
    signals.append(SignalResult("S07", "has_design", has_design, weight=1.0,
                                evidence=f"screen count={screen_count}"))

    # Weighted average maturity
    total_weight = sum(s.weight for s in signals)
    maturity = sum(s.value * s.weight for s in signals) / total_weight if total_weight else 0.0
    maturity = round(min(1.0, max(0.0, maturity)), 4)

    # Deterministic hash
    canon = json.dumps({
        "project_id": project_id,
        "maturity": maturity,
        "signals": [{"id": s.signal_id, "value": s.value} for s in signals],
    }, sort_keys=True, separators=(",", ":")).encode()
    snap_hash = f"sha256:{hashlib.sha256(canon).hexdigest()}"

    return ProgressSnapshot(
        project_id=project_id,
        stage=current_stage,
        maturity=maturity,
        signals=signals,
        snapshot_hash=snap_hash,
    )


def advance_stage(snapshot: ProgressSnapshot) -> ProgressSnapshot:
    """
    Return a new snapshot with the stage advanced (if maturity allows).
    Does NOT mutate the original.
    """
    if not snapshot.can_advance():
        return snapshot
    next_idx = snapshot.stage_index + 1
    new_stage = _STAGE_ORDER[next_idx]
    import copy
    new_snap = copy.copy(snapshot)
    new_snap.stage = new_stage
    new_snap.computed_at = time.monotonic()
    return new_snap


# =============================================================================
# TSK-075: Evolution engine — triggers, operators, proposals
# =============================================================================

class TriggerKind(str, Enum):
    STALENESS      = "staleness"       # upstream changed → binding stale
    PROGRESS_GATE  = "progress_gate"   # stage maturity crossed threshold
    MISSING_TYPE   = "missing_type"    # required artifact type absent
    QUALITY_DROP   = "quality_drop"    # quality score fell below threshold


@dataclass
class EvolutionTrigger:
    """An event that the evolution engine detected and must act on."""
    trigger_id: str
    kind: TriggerKind
    project_id: str
    detail: dict[str, Any] = field(default_factory=dict)
    detected_at: float = field(default_factory=time.monotonic)


@dataclass
class EvolutionProposal:
    """
    A reviewable proposal emitted by the evolution engine.
    NEVER auto-applied — always requires human review.
    """
    proposal_id: str
    trigger_id: str
    operator: str             # which operator produced this
    description: str
    suggested_binding_id: str | None = None   # which field run to invoke
    suggested_artifact_type: str | None = None
    suggested_field_path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    auto_run: bool = False    # ALWAYS False — suggestions never auto-run (TSK-076)


class EvolutionEngine:
    """
    Monitors project state changes and emits EvolutionProposals.
    Key invariant: proposals are NEVER applied automatically.
    """

    def __init__(self) -> None:
        self._proposals: list[EvolutionProposal] = []

    def evaluate(
        self,
        project_id: str,
        snapshot: ProgressSnapshot,
        stale_bindings: list[Any] | None = None,
        artifact_summary: ArtifactSummary | None = None,
    ) -> list[EvolutionProposal]:
        """
        Evaluate the current project state and return new proposals.
        Never auto-applies anything.
        """
        import hashlib, time as _time
        new_proposals: list[EvolutionProposal] = []

        # Operator 1: Staleness — propose re-runs for stale fields
        if stale_bindings:
            for stale in stale_bindings:
                trigger = EvolutionTrigger(
                    trigger_id=f"trig:stale:{stale.binding_id}:{stale.artifact_id}",
                    kind=TriggerKind.STALENESS,
                    project_id=project_id,
                    detail={
                        "binding_id": stale.binding_id,
                        "artifact_id": stale.artifact_id,
                        "field_path": stale.field_path,
                    },
                )
                prop = EvolutionProposal(
                    proposal_id=f"prop:{hashlib.sha256(trigger.trigger_id.encode()).hexdigest()[:12]}",
                    trigger_id=trigger.trigger_id,
                    operator="staleness_operator",
                    description=(
                        f"Field {stale.field_path!r} on artifact {stale.artifact_id!r} "
                        f"may be stale. Consider re-running binding {stale.binding_id!r}."
                    ),
                    suggested_binding_id=stale.binding_id,
                    suggested_artifact_type=None,
                    suggested_field_path=stale.field_path,
                    auto_run=False,
                )
                new_proposals.append(prop)

        # Operator 2: Missing types — propose creating required artifact types
        if artifact_summary:
            required_for_stage = {
                ProjectStage.DISCOVERY: ["brief"],
                ProjectStage.IDEATION: ["brief", "persona"],
                ProjectStage.DEFINITION: ["brief", "persona", "user_story", "requirement"],
                ProjectStage.DESIGN: ["brief", "persona", "user_story", "screen"],
                ProjectStage.DELIVERY: ["brief", "persona", "user_story", "requirement", "screen"],
            }
            for atype in required_for_stage.get(snapshot.stage, []):
                if artifact_summary.type_counts.get(atype, 0) == 0:
                    trigger = EvolutionTrigger(
                        trigger_id=f"trig:missing:{project_id}:{atype}",
                        kind=TriggerKind.MISSING_TYPE,
                        project_id=project_id,
                        detail={"missing_type": atype, "stage": snapshot.stage},
                    )
                    prop = EvolutionProposal(
                        proposal_id=f"prop:{hashlib.sha256(trigger.trigger_id.encode()).hexdigest()[:12]}",
                        trigger_id=trigger.trigger_id,
                        operator="missing_type_operator",
                        description=f"Stage {snapshot.stage!r} requires at least one {atype!r} artifact.",
                        suggested_artifact_type=atype,
                        auto_run=False,
                    )
                    new_proposals.append(prop)

        # Operator 3: Progress gate — suggest stage advance if maturity high enough
        if snapshot.can_advance():
            trigger = EvolutionTrigger(
                trigger_id=f"trig:gate:{project_id}:{snapshot.stage}",
                kind=TriggerKind.PROGRESS_GATE,
                project_id=project_id,
                detail={"stage": snapshot.stage, "maturity": snapshot.maturity},
            )
            prop = EvolutionProposal(
                proposal_id=f"prop:{hashlib.sha256(trigger.trigger_id.encode()).hexdigest()[:12]}",
                trigger_id=trigger.trigger_id,
                operator="progress_gate_operator",
                description=(
                    f"Project maturity is {snapshot.maturity:.0%}. "
                    f"Consider advancing from {snapshot.stage!r} to the next stage."
                ),
                auto_run=False,
            )
            new_proposals.append(prop)

        self._proposals.extend(new_proposals)
        return new_proposals

    def all_proposals(self) -> list[EvolutionProposal]:
        return list(self._proposals)

    def pending_count(self) -> int:
        return len(self._proposals)


# =============================================================================
# TSK-076: Skill unlock rules
# =============================================================================

@dataclass
class SkillUnlockRule:
    """Defines when a skill becomes available based on project stage/maturity."""
    skill_id: str
    min_stage: ProjectStage
    min_maturity: float = 0.0
    description: str = ""


_DEFAULT_UNLOCK_RULES: list[SkillUnlockRule] = [
    SkillUnlockRule("builtin:discovery",    ProjectStage.DISCOVERY,  0.0,  "Always available"),
    SkillUnlockRule("builtin:requirements", ProjectStage.IDEATION,   0.3,  "Available after ideation starts"),
    SkillUnlockRule("builtin:critic",       ProjectStage.DEFINITION, 0.5,  "Available once definition is 50% mature"),
    SkillUnlockRule("builtin:design",       ProjectStage.DESIGN,     0.4,  "Available in design stage"),
    SkillUnlockRule("builtin:delivery",     ProjectStage.DELIVERY,   0.6,  "Available in delivery stage"),
]


def check_skill_unlocked(
    skill_id: str,
    snapshot: ProgressSnapshot,
    rules: list[SkillUnlockRule] | None = None,
) -> tuple[bool, str]:
    """
    Check whether a skill is unlocked for the current project state.
    Returns (unlocked, reason).
    TSK-076: Suggestions never auto-run regardless of unlock status.
    """
    rules = rules or _DEFAULT_UNLOCK_RULES
    rule = next((r for r in rules if r.skill_id == skill_id), None)
    if rule is None:
        return True, "No unlock rule — available by default"

    stage_ok = _STAGE_ORDER.index(snapshot.stage) >= _STAGE_ORDER.index(rule.min_stage)
    maturity_ok = snapshot.maturity >= rule.min_maturity

    if not stage_ok:
        return False, (
            f"Requires stage {rule.min_stage!r}; current stage is {snapshot.stage!r}"
        )
    if not maturity_ok:
        return False, (
            f"Requires maturity {rule.min_maturity:.0%}; current maturity is {snapshot.maturity:.0%}"
        )
    return True, rule.description
