"""
Tests for EPIC-08:
  TSK-070: Prompt assets, versions, blocks, variables
  TSK-071: Prompt runs with DNA pinning and usage accounting
  TSK-073: Evaluation cases, runs, comparison
  TSK-074: Progress model computation + snapshots
  TSK-075: Evolution engine — triggers, operators, proposals
  TSK-076: Skill unlock rules + stage rail
"""
from __future__ import annotations

import pytest

# =============================================================================
# TSK-070: Prompt assets
# =============================================================================

from backend.app.prompts.assets import (
    BlockKind,
    PromptAsset,
    PromptBlock,
    PromptVariable,
    PromptVersion,
    VariableKind,
    new_version,
    render_prompt,
)


def _make_asset(aid: str = "pa1", name: str = "test-asset") -> PromptAsset:
    return PromptAsset(id=aid, name=name, description="Test prompt asset")


def _make_simple_version(asset: PromptAsset) -> PromptVersion:
    return new_version(
        asset,
        blocks=[PromptBlock(BlockKind.SYSTEM, "You are a helpful assistant."),
                PromptBlock(BlockKind.USER, "Write a {{artifact_type}} body for: {{title}}")],
        variables=[
            PromptVariable("artifact_type", VariableKind.STRING, default_value="user story"),
            PromptVariable("title", VariableKind.STRING),
        ],
    )


class TestPromptVariable:
    def test_secret_variable_no_default(self):
        with pytest.raises(ValueError, match="secret"):
            PromptVariable("key", VariableKind.SECRET, default_value="oops")

    def test_string_variable_ok(self):
        v = PromptVariable("name", VariableKind.STRING, default_value="Alice")
        assert v.default_value == "Alice"

    def test_secret_ref_stored(self):
        v = PromptVariable("api_key", VariableKind.SECRET, secret_ref="vault:openai/key")
        assert v.secret_ref == "vault:openai/key"


class TestPromptVersion:
    def test_seal_computes_hash(self):
        asset = _make_asset()
        version = _make_simple_version(asset)
        assert version.sealed is True
        assert version.content_hash.startswith("sha256:")

    def test_sealed_version_immutable(self):
        asset = _make_asset()
        version = _make_simple_version(asset)
        with pytest.raises(AttributeError):
            version.blocks = []

    def test_version_number_increments(self):
        asset = _make_asset()
        v1 = _make_simple_version(asset)
        v2 = new_version(asset,
                         blocks=[PromptBlock(BlockKind.USER, "hello")],
                         variables=[])
        assert v1.version_number == 1
        assert v2.version_number == 2

    def test_undefined_variable_in_block_raises(self):
        asset = _make_asset()
        with pytest.raises(ValueError, match="undefined variable"):
            new_version(asset,
                        blocks=[PromptBlock(BlockKind.USER, "{{undefined}}")],
                        variables=[])


class TestPromptAsset:
    def test_add_sealed_version(self):
        asset = _make_asset()
        _make_simple_version(asset)
        assert len(asset.versions) == 1

    def test_add_unsealed_raises(self):
        asset = _make_asset()
        v = PromptVersion("v1", "pa1", 1, [], [])
        with pytest.raises(ValueError, match="sealed"):
            asset.add_version(v)

    def test_latest_version(self):
        asset = _make_asset()
        v1 = _make_simple_version(asset)
        assert asset.latest_version() is v1

    def test_get_version_by_number(self):
        asset = _make_asset()
        _make_simple_version(asset)
        assert asset.get_version(1) is not None
        assert asset.get_version(99) is None


class TestRenderPrompt:
    def test_basic_render(self):
        asset = _make_asset()
        v = _make_simple_version(asset)
        result = render_prompt(v, {"artifact_type": "story", "title": "Login flow"})
        assert "story" in result
        assert "Login flow" in result

    def test_default_value_used(self):
        asset = _make_asset()
        v = _make_simple_version(asset)
        result = render_prompt(v, {"title": "My title"})
        assert "user story" in result  # default for artifact_type

    def test_missing_required_raises(self):
        asset = _make_asset()
        v = _make_simple_version(asset)
        with pytest.raises(KeyError):
            render_prompt(v, {})

    def test_allow_missing_does_not_raise(self):
        asset = _make_asset()
        v = _make_simple_version(asset)
        result = render_prompt(v, {}, allow_missing=True)
        assert isinstance(result, str)


# =============================================================================
# TSK-071: Prompt runs + DNA pinning
# =============================================================================

from backend.app.prompts.runs import (
    PromptRun,
    create_prompt_run,
    rerun_from_pinned,
)


class TestCreatePromptRun:
    def _version(self) -> PromptVersion:
        asset = _make_asset()
        return _make_simple_version(asset)

    def test_creates_run(self):
        v = self._version()
        run = create_prompt_run(
            run_id="r1",
            version=v,
            variable_values={"artifact_type": "story", "title": "Login"},
            raw_output="As a user I can log in.",
        )
        assert isinstance(run, PromptRun)
        assert run.run_id == "r1"

    def test_input_hash_matches_rendered(self):
        import hashlib
        v = self._version()
        run = create_prompt_run(
            run_id="r1",
            version=v,
            variable_values={"artifact_type": "story", "title": "Login"},
        )
        expected = f"sha256:{hashlib.sha256(run.inputs.rendered_prompt.encode()).hexdigest()}"
        assert run.inputs.input_hash == expected

    def test_tokens_recorded(self):
        v = self._version()
        run = create_prompt_run(
            run_id="r1",
            version=v,
            variable_values={"artifact_type": "story", "title": "Login"},
            raw_output="some output",
        )
        assert run.tokens_input > 0
        assert run.tokens_output > 0
        assert run.total_tokens > 0

    def test_trace_id_set(self):
        v = self._version()
        run = create_prompt_run(
            run_id="r1", version=v,
            variable_values={"artifact_type": "story", "title": "X"},
        )
        assert run.trace_id.startswith("trace:")

    def test_version_hash_pinned(self):
        v = self._version()
        run = create_prompt_run(
            run_id="r1", version=v,
            variable_values={"artifact_type": "story", "title": "X"},
        )
        assert run.inputs.version_hash == v.content_hash

    def test_deterministic_input_hash(self):
        v = self._version()
        vars_ = {"artifact_type": "story", "title": "X"}
        r1 = create_prompt_run(run_id="r1", version=v, variable_values=vars_)
        r2 = create_prompt_run(run_id="r2", version=v, variable_values=vars_)
        assert r1.inputs.input_hash == r2.inputs.input_hash


class TestRerunFromPinned:
    def _version(self) -> PromptVersion:
        asset = _make_asset()
        return _make_simple_version(asset)

    def test_rerun_uses_same_inputs(self):
        v = self._version()
        original = create_prompt_run(
            run_id="r1", version=v,
            variable_values={"artifact_type": "story", "title": "Login"},
        )
        rerun = rerun_from_pinned(original, new_run_id="r2", version=v, new_output="new output")
        assert rerun.inputs.variable_values == original.inputs.variable_values
        assert rerun.inputs.input_hash == original.inputs.input_hash

    def test_rerun_wrong_version_raises(self):
        v1 = self._version()
        original = create_prompt_run(
            run_id="r1", version=v1,
            variable_values={"artifact_type": "story", "title": "X"},
        )
        # Create a different asset/version
        v2 = new_version(
            _make_asset("pa2"), [PromptBlock(BlockKind.USER, "different")], []
        )
        with pytest.raises(ValueError, match="hash mismatch"):
            rerun_from_pinned(original, new_run_id="r2", version=v2)


# =============================================================================
# TSK-073: Evaluation
# =============================================================================

from backend.app.prompts.runs import (
    EvaluationCase,
    EvaluationRun,
    EvalVerdict,
    RubricCriterion,
    evaluate_output,
    run_evaluation,
)


class TestEvaluationCase:
    def test_pass_when_contains_expected(self):
        case = EvaluationCase(
            case_id="c1", asset_id="pa1",
            description="Check login",
            variable_values={},
            expected_contains=["log in"],
        )
        result = evaluate_output(case, "As a user I can log in.", "r1")
        assert result.verdict == EvalVerdict.PASS

    def test_fail_when_missing_expected(self):
        case = EvaluationCase(
            case_id="c1", asset_id="pa1",
            description="Check login",
            variable_values={},
            expected_contains=["payment"],
        )
        result = evaluate_output(case, "As a user I can log in.", "r1")
        assert result.verdict == EvalVerdict.FAIL
        assert len(result.failures) > 0

    def test_fail_when_forbidden_present(self):
        case = EvaluationCase(
            case_id="c1", asset_id="pa1",
            description="No PII",
            variable_values={},
            expected_not_contains=["password"],
        )
        result = evaluate_output(case, "The password is 1234.", "r1")
        assert result.verdict == EvalVerdict.FAIL

    def test_rubric_scores_all_criteria(self):
        case = EvaluationCase(
            case_id="c1", asset_id="pa1",
            description="Quality check",
            variable_values={},
            rubric=[
                RubricCriterion("clarity", "Is it clear?", weight=1.0),
                RubricCriterion("completeness", "Is it complete?", weight=2.0),
            ],
        )
        result = evaluate_output(case, "A clear and complete response.", "r1")
        assert "clarity" in result.rubric_scores
        assert "completeness" in result.rubric_scores

    def test_overall_score_range(self):
        case = EvaluationCase(
            case_id="c1", asset_id="pa1",
            description="d", variable_values={},
        )
        result = evaluate_output(case, "any output", "r1")
        assert 0.0 <= result.overall_score <= 1.0


class TestEvaluationRun:
    def test_run_evaluation_counts(self):
        cases = [
            EvaluationCase("c1", "pa1", "d", {}, expected_contains=["yes"]),
            EvaluationCase("c2", "pa1", "d", {}, expected_contains=["yes"]),
            EvaluationCase("c3", "pa1", "d", {}, expected_contains=["yes"]),
        ]
        outputs = {"c1": "yes", "c2": "no", "c3": "yes"}
        run_ids = {"c1": "r1", "c2": "r2", "c3": "r3"}
        ev_run = run_evaluation("ev1", cases, outputs, run_ids)
        assert isinstance(ev_run, EvaluationRun)
        assert ev_run.pass_count == 2
        assert ev_run.fail_count == 1

    def test_pass_rate(self):
        cases = [EvaluationCase(f"c{i}", "pa1", "d", {}) for i in range(4)]
        outputs = {f"c{i}": "ok" for i in range(4)}
        run_ids = {f"c{i}": f"r{i}" for i in range(4)}
        ev_run = run_evaluation("ev1", cases, outputs, run_ids)
        assert ev_run.pass_rate == 1.0

    def test_average_score(self):
        cases = [EvaluationCase("c1", "pa1", "d", {})]
        ev_run = run_evaluation("ev1", cases, {"c1": "output"}, {"c1": "r1"})
        assert 0.0 <= ev_run.average_score <= 1.0


# =============================================================================
# TSK-074: Progress model
# =============================================================================

from backend.app.evolution.engine import (
    ArtifactSummary,
    EvolutionEngine,
    EvolutionProposal,
    ProjectStage,
    ProgressSnapshot,
    SkillUnlockRule,
    TriggerKind,
    advance_stage,
    check_skill_unlocked,
    compute_progress,
)


class TestProgressModel:
    def _full_artifacts(self) -> ArtifactSummary:
        return ArtifactSummary(
            type_counts={
                "brief": 1, "persona": 2, "user_story": 5,
                "requirement": 6, "decision": 3, "screen": 3,
            },
            quality_scores={"user_story": 0.9},
            total=20,
        )

    def _empty_artifacts(self) -> ArtifactSummary:
        return ArtifactSummary(type_counts={}, quality_scores={}, total=0)

    def test_compute_returns_snapshot(self):
        snap = compute_progress("p1", self._full_artifacts())
        assert isinstance(snap, ProgressSnapshot)

    def test_full_project_high_maturity(self):
        snap = compute_progress("p1", self._full_artifacts())
        assert snap.maturity > 0.7

    def test_empty_project_low_maturity(self):
        snap = compute_progress("p1", self._empty_artifacts())
        assert snap.maturity < 0.3

    def test_deterministic_hash(self):
        arts = self._full_artifacts()
        h1 = compute_progress("p1", arts).snapshot_hash
        h2 = compute_progress("p1", arts).snapshot_hash
        assert h1 == h2

    def test_signals_all_present(self):
        snap = compute_progress("p1", self._full_artifacts())
        assert len(snap.signals) >= 7

    def test_can_advance_when_mature(self):
        snap = compute_progress("p1", self._full_artifacts())
        assert snap.can_advance() is True

    def test_cannot_advance_when_immature(self):
        snap = compute_progress("p1", self._empty_artifacts())
        assert snap.can_advance() is False

    def test_advance_stage_increments(self):
        snap = compute_progress("p1", self._full_artifacts(),
                                current_stage=ProjectStage.DISCOVERY)
        advanced = advance_stage(snap)
        assert advanced.stage == ProjectStage.IDEATION

    def test_advance_at_delivery_no_change(self):
        snap = compute_progress("p1", self._full_artifacts(),
                                current_stage=ProjectStage.DELIVERY)
        advanced = advance_stage(snap)
        assert advanced.stage == ProjectStage.DELIVERY   # already at end


# =============================================================================
# TSK-075: Evolution engine
# =============================================================================

class TestEvolutionEngine:
    def _snapshot(self, stage=ProjectStage.DISCOVERY, maturity=0.8) -> ProgressSnapshot:
        from dataclasses import replace
        snap = compute_progress("p1", ArtifactSummary(
            type_counts={"brief": 1, "persona": 1, "user_story": 3,
                         "requirement": 5, "decision": 2, "screen": 2},
            quality_scores={"user_story": 0.9},
        ))
        # Override stage + maturity for deterministic tests
        import copy
        s = copy.copy(snap)
        s.stage = stage
        s.maturity = maturity
        return s

    def test_no_stale_no_staleness_proposals(self):
        engine = EvolutionEngine()
        proposals = engine.evaluate("p1", self._snapshot(), stale_bindings=[])
        stale = [p for p in proposals if p.operator == "staleness_operator"]
        assert len(stale) == 0

    def test_stale_binding_emits_proposal(self):
        from backend.app.bindings.staleness import StalenessReport
        engine = EvolutionEngine()
        stale = [StalenessReport("b1", "art1", "body", ["req1"], "evidence")]
        proposals = engine.evaluate("p1", self._snapshot(), stale_bindings=stale)
        staleness_props = [p for p in proposals if p.operator == "staleness_operator"]
        assert len(staleness_props) == 1

    def test_missing_type_emits_proposal(self):
        engine = EvolutionEngine()
        # Empty artifacts → missing types
        empty_snap = compute_progress("p1", ArtifactSummary(type_counts={}, quality_scores={}))
        arts = ArtifactSummary(type_counts={}, quality_scores={})
        proposals = engine.evaluate("p1", empty_snap, artifact_summary=arts)
        missing = [p for p in proposals if p.operator == "missing_type_operator"]
        assert len(missing) > 0

    def test_progress_gate_emits_proposal(self):
        engine = EvolutionEngine()
        snap = self._snapshot(maturity=0.8)
        proposals = engine.evaluate("p1", snap)
        gate = [p for p in proposals if p.operator == "progress_gate_operator"]
        assert len(gate) > 0

    def test_proposals_never_auto_run(self):
        engine = EvolutionEngine()
        snap = self._snapshot(maturity=0.8)
        proposals = engine.evaluate("p1", snap)
        for prop in proposals:
            assert prop.auto_run is False, f"Proposal {prop.proposal_id} has auto_run=True!"

    def test_proposals_accumulated(self):
        engine = EvolutionEngine()
        snap = self._snapshot(maturity=0.8)
        engine.evaluate("p1", snap)
        engine.evaluate("p1", snap)
        assert engine.pending_count() > 1


# =============================================================================
# TSK-076: Skill unlock rules
# =============================================================================

class TestSkillUnlockRules:
    def _snap(self, stage: ProjectStage, maturity: float) -> ProgressSnapshot:
        import copy
        base = compute_progress("p1", ArtifactSummary(type_counts={}, quality_scores={}))
        s = copy.copy(base)
        s.stage = stage
        s.maturity = maturity
        return s

    def test_discovery_skill_always_unlocked(self):
        snap = self._snap(ProjectStage.DISCOVERY, 0.0)
        unlocked, _ = check_skill_unlocked("builtin:discovery", snap)
        assert unlocked is True

    def test_requirements_locked_in_discovery(self):
        snap = self._snap(ProjectStage.DISCOVERY, 0.5)
        unlocked, reason = check_skill_unlocked("builtin:requirements", snap)
        assert unlocked is False
        assert "stage" in reason.lower()

    def test_requirements_unlocked_in_ideation(self):
        snap = self._snap(ProjectStage.IDEATION, 0.4)
        unlocked, _ = check_skill_unlocked("builtin:requirements", snap)
        assert unlocked is True

    def test_maturity_threshold_enforced(self):
        # critic requires definition stage + 0.5 maturity
        snap = self._snap(ProjectStage.DEFINITION, 0.2)  # too low maturity
        unlocked, reason = check_skill_unlocked("builtin:critic", snap)
        assert unlocked is False
        assert "maturity" in reason.lower()

    def test_unknown_skill_always_unlocked(self):
        snap = self._snap(ProjectStage.DISCOVERY, 0.0)
        unlocked, reason = check_skill_unlocked("custom:unknown-skill", snap)
        assert unlocked is True
        assert "default" in reason.lower()
