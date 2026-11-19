"""
Tests for TSK-057: Orchestrator (state machine + checkpointer).
Tests for TSK-058: Specialist workflows (discovery, requirements, critic).
Tests for TSK-059: Model adapter (provider-neutral, schema, retries).
"""
from __future__ import annotations

import pytest

# ============================================================================
# TSK-057: Orchestrator
# ============================================================================

from backend.app.ai_runtime.orchestrator import (
    Checkpointer,
    NodeName,
    Orchestrator,
    OrchestratorState,
)


class TestCheckpointer:
    def test_save_and_load(self):
        cp = Checkpointer()
        state = OrchestratorState(run_id="r1", project_id="p1", goal="write story")
        cp.save(state)
        loaded = cp.load("r1")
        assert loaded is not None
        assert loaded.run_id == "r1"

    def test_load_missing_returns_none(self):
        cp = Checkpointer()
        assert cp.load("ghost") is None

    def test_delete(self):
        cp = Checkpointer()
        state = OrchestratorState(run_id="r1", project_id="p1", goal="test")
        cp.save(state)
        cp.delete("r1")
        assert cp.load("r1") is None

    def test_list_runs(self):
        cp = Checkpointer()
        cp.save(OrchestratorState(run_id="r1", project_id="p1", goal="a"))
        cp.save(OrchestratorState(run_id="r2", project_id="p1", goal="b"))
        assert set(cp.list_runs()) == {"r1", "r2"}


class TestOrchestrator:
    def test_start_reaches_human_review(self):
        orch = Orchestrator()
        state = orch.start(run_id="r1", project_id="p1", goal="write user story body")
        assert state.current_node == NodeName.HUMAN_REVIEW

    def test_plan_populated_after_start(self):
        orch = Orchestrator()
        state = orch.start(run_id="r1", project_id="p1", goal="write user story")
        assert len(state.plan) > 0

    def test_proposals_populated_after_start(self):
        orch = Orchestrator()
        state = orch.start(run_id="r1", project_id="p1", goal="write user story")
        assert len(state.proposals) > 0

    def test_checkpoint_saved_at_pause(self):
        cp = Checkpointer()
        orch = Orchestrator(checkpointer=cp)
        orch.start(run_id="r1", project_id="p1", goal="write user story")
        assert cp.load("r1") is not None

    def test_resume_approve_reaches_done(self):
        orch = Orchestrator()
        orch.start(run_id="r1", project_id="p1", goal="write user story")
        state = orch.resume("r1", decision="approve")
        assert state.current_node == NodeName.DONE

    def test_resume_reject_reaches_done_rejected(self):
        orch = Orchestrator()
        orch.start(run_id="r1", project_id="p1", goal="write user story")
        state = orch.resume("r1", decision="reject")
        assert state.current_node == NodeName.DONE
        assert state.result.get("status") == "rejected"

    def test_resume_with_edits(self):
        orch = Orchestrator()
        orch.start(run_id="r1", project_id="p1", goal="write user story")
        state = orch.resume("r1", decision="edit", edits={"body": "custom body"})
        assert state.current_node == NodeName.DONE
        assert state.result["fields"].get("body") == "custom body"

    def test_resume_unknown_run_raises(self):
        orch = Orchestrator()
        with pytest.raises(KeyError):
            orch.resume("ghost-run", decision="approve")

    def test_resume_non_paused_raises(self):
        orch = Orchestrator()
        orch.start(run_id="r1", project_id="p1", goal="write user story")
        orch.resume("r1", decision="approve")   # now at DONE
        with pytest.raises(RuntimeError):
            orch.resume("r1", decision="approve")

    def test_restart_from_checkpoint(self):
        """Simulate a restart: create new Orchestrator with same checkpointer."""
        cp = Checkpointer()
        orch1 = Orchestrator(checkpointer=cp)
        orch1.start(run_id="r1", project_id="p1", goal="write story")
        # Restart with new Orchestrator but same checkpointer
        orch2 = Orchestrator(checkpointer=cp)
        state = orch2.load("r1")
        assert state is not None
        assert state.current_node == NodeName.HUMAN_REVIEW

    def test_checkpoint_hash_deterministic(self):
        state = OrchestratorState(run_id="r1", project_id="p1", goal="test")
        h1 = state.checkpoint_hash()
        h2 = state.checkpoint_hash()
        assert h1 == h2


# ============================================================================
# TSK-058: Specialists
# ============================================================================

from backend.app.ai_runtime.specialists import (
    CriticSpecialist,
    DiscoverySpecialist,
    RequirementsSpecialist,
    ReviewReport,
    SpecialistKind,
    SpecialistResult,
)


class TestDiscoverySpecialist:
    def test_returns_specialist_result(self):
        ds = DiscoverySpecialist()
        result = ds.run(run_id="r1", project_summary="A todo app")
        assert isinstance(result, SpecialistResult)
        assert result.specialist == SpecialistKind.DISCOVERY

    def test_suggests_missing_types(self):
        ds = DiscoverySpecialist()
        result = ds.run(run_id="r1", project_summary="A todo app", existing_types=[])
        types = {a.artifact_type for a in result.artifacts}
        assert "brief" in types

    def test_skips_existing_types(self):
        ds = DiscoverySpecialist()
        result = ds.run(
            run_id="r1",
            project_summary="A todo app",
            existing_types=["brief", "persona", "user_story", "requirement"],
        )
        types = {a.artifact_type for a in result.artifacts}
        assert "brief" not in types

    def test_hint_adds_question_artifact(self):
        ds = DiscoverySpecialist()
        result = ds.run(run_id="r1", project_summary="todo", hint="What is the target audience?")
        types = {a.artifact_type for a in result.artifacts}
        assert "question" in types

    def test_max_steps_respected(self):
        ds = DiscoverySpecialist(max_steps=2)
        result = ds.run(run_id="r1", project_summary="todo", hint="hint")
        assert result.steps_taken <= 2

    def test_all_artifacts_typed(self):
        ds = DiscoverySpecialist()
        result = ds.run(run_id="r1", project_summary="todo")
        for a in result.artifacts:
            assert a.artifact_type, "artifact_type must be non-empty"
            assert a.title, "title must be non-empty"


class TestRequirementsSpecialist:
    def test_returns_specialist_result(self):
        rs = RequirementsSpecialist()
        result = rs.run(run_id="r1", user_intent="log in with email")
        assert isinstance(result, SpecialistResult)
        assert result.specialist == SpecialistKind.REQUIREMENTS

    def test_produces_user_story(self):
        rs = RequirementsSpecialist()
        result = rs.run(run_id="r1", user_intent="log in with email")
        types = {a.artifact_type for a in result.artifacts}
        assert "user_story" in types

    def test_produces_requirement(self):
        rs = RequirementsSpecialist()
        result = rs.run(run_id="r1", user_intent="log in with email")
        types = {a.artifact_type for a in result.artifacts}
        assert "requirement" in types

    def test_story_body_mentions_persona(self):
        rs = RequirementsSpecialist()
        result = rs.run(run_id="r1", user_intent="log in", persona_name="admin")
        story = next(a for a in result.artifacts if a.artifact_type == "user_story")
        assert "admin" in story.body

    def test_acceptance_criteria_in_payload(self):
        rs = RequirementsSpecialist()
        result = rs.run(run_id="r1", user_intent="log in with email")
        story = next(a for a in result.artifacts if a.artifact_type == "user_story")
        assert "acceptance_criteria" in story.payload
        assert isinstance(story.payload["acceptance_criteria"], list)


class TestCriticSpecialist:
    def test_returns_review_report(self):
        critic = CriticSpecialist()
        report = critic.review(
            run_id="r1",
            artifact_type="user_story",
            field_path="body",
            proposed_value="As a user I want to log in.",
        )
        assert isinstance(report, ReviewReport)

    def test_valid_string_approved(self):
        critic = CriticSpecialist()
        report = critic.review(
            run_id="r1",
            artifact_type="user_story",
            field_path="body",
            proposed_value="As a user I want to log in with my email and password.",
            schema={"type": "string"},
        )
        assert report.approved is True

    def test_wrong_type_not_approved(self):
        critic = CriticSpecialist()
        report = critic.review(
            run_id="r1",
            artifact_type="user_story",
            field_path="body",
            proposed_value=123,
            schema={"type": "string"},
        )
        assert report.approved is False
        assert any(a.severity == "error" for a in report.annotations)

    def test_missing_required_field_error(self):
        critic = CriticSpecialist()
        report = critic.review(
            run_id="r1",
            artifact_type="persona",
            field_path="body",
            proposed_value={"name": "Alice"},
            schema={"type": "object"},
            required_fields=["name", "goal"],
        )
        errors = [a for a in report.annotations if a.severity == "error"]
        assert any("goal" in e.message for e in errors)

    def test_critic_cannot_mutate(self):
        """CriticSpecialist.review() returns ReviewReport — no patch, no mutation."""
        critic = CriticSpecialist()
        original = "As a user I want to log in."
        report = critic.review(
            run_id="r1",
            artifact_type="user_story",
            field_path="body",
            proposed_value=original,
        )
        # Report does not carry patches or mutations
        assert not hasattr(report, "patch")
        assert not hasattr(report, "mutations")
        assert isinstance(report, ReviewReport)

    def test_score_range(self):
        critic = CriticSpecialist()
        report = critic.review(
            run_id="r1",
            artifact_type="user_story",
            field_path="body",
            proposed_value="short",
            schema={"type": "string"},
        )
        assert 0.0 <= report.overall_score <= 1.0


# ============================================================================
# TSK-059: Model adapter
# ============================================================================

from backend.app.ai_runtime.model_adapter import (
    GenerationResult,
    ModelAdapter,
    StubProvider,
    _validate_schema,
    get_provider,
    register_provider,
)


class TestStubProvider:
    def test_returns_string(self):
        p = StubProvider()
        result = p.complete([{"role": "user", "content": "hello"}])
        assert isinstance(result, str)

    def test_json_mode_returns_valid_json(self):
        p = StubProvider()
        raw = p.complete(
            [{"role": "user", "content": "hi"}],
            json_mode=True,
            schema={"type": "object"},
        )
        import json
        parsed = json.loads(raw)
        assert isinstance(parsed, dict)

    def test_array_schema_returns_list(self):
        p = StubProvider()
        raw = p.complete(
            [{"role": "user", "content": "hi"}],
            json_mode=True,
            schema={"type": "array"},
        )
        import json
        parsed = json.loads(raw)
        assert isinstance(parsed, list)

    def test_deterministic_for_same_input(self):
        p = StubProvider()
        msgs = [{"role": "user", "content": "same input"}]
        r1 = p.complete(msgs)
        r2 = p.complete(msgs)
        assert r1 == r2


class TestSchemaValidation:
    def test_string_ok(self):
        assert _validate_schema("hello", {"type": "string"}) == []

    def test_string_wrong_type(self):
        v = _validate_schema(123, {"type": "string"})
        assert len(v) > 0

    def test_array_ok(self):
        assert _validate_schema([], {"type": "array"}) == []

    def test_object_missing_required(self):
        v = _validate_schema({"name": "x"}, {"type": "object", "required": ["name", "goal"]})
        assert any("goal" in s for s in v)

    def test_min_length_violation(self):
        v = _validate_schema("hi", {"type": "string", "minLength": 10})
        assert len(v) > 0

    def test_max_items_violation(self):
        v = _validate_schema([1, 2, 3, 4], {"type": "array", "maxItems": 2})
        assert len(v) > 0


class TestModelAdapter:
    def test_generate_string(self):
        adapter = ModelAdapter(provider="stub")
        result = adapter.generate(user_prompt="write a story", schema={"type": "string"})
        assert isinstance(result, GenerationResult)
        assert isinstance(result.value, str)
        assert result.schema_valid is True

    def test_generate_array(self):
        adapter = ModelAdapter(provider="stub")
        result = adapter.generate(user_prompt="list items", schema={"type": "array"})
        assert result.schema_valid is True
        assert isinstance(result.value, list)

    def test_generate_object(self):
        adapter = ModelAdapter(provider="stub")
        result = adapter.generate(user_prompt="describe user", schema={"type": "object"})
        assert result.schema_valid is True
        assert isinstance(result.value, dict)

    def test_attempts_recorded(self):
        adapter = ModelAdapter(provider="stub")
        result = adapter.generate(user_prompt="write story", schema={"type": "string"})
        assert result.attempts >= 1

    def test_tokens_used_positive(self):
        adapter = ModelAdapter(provider="stub")
        result = adapter.generate(user_prompt="write story", schema={"type": "string"})
        assert result.tokens_used > 0

    def test_provider_neutral_switch(self):
        register_provider("stub2", StubProvider())  # type: ignore[arg-type]
        adapter = ModelAdapter(provider="stub")
        adapter.switch_provider("stub2")
        result = adapter.generate(user_prompt="write story", schema={"type": "string"})
        assert result.provider == "stub2"

    def test_unknown_provider_raises(self):
        with pytest.raises(KeyError):
            ModelAdapter(provider="nonexistent")

    def test_system_prompt_included(self):
        adapter = ModelAdapter(provider="stub")
        result = adapter.generate(
            system_prompt="You are a helpful assistant.",
            user_prompt="write",
            schema={"type": "string"},
        )
        assert result.schema_valid is True
