"""
Tests for TSK-042: Field run endpoint + streaming proposal.

Acceptance: Returns schema-valid proposal; never writes directly; cost recorded.
"""
from __future__ import annotations

import pytest

from backend.app.bindings.assembler import ArtifactContext
from backend.app.bindings.field_run import (
    FieldRunError,
    FieldRunRequest,
    FieldRunResult,
    run_field,
)
from backend.app.bindings.models import (
    AutoApplyPolicy,
    BindingPolicy,
    BindingScope,
    ContextRule,
    FieldBinding,
    OutputContract,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_binding(
    bid: str = "b1",
    artifact_type: str = "user_story",
    field_path: str = "body",
    *,
    locked: bool = False,
    cooldown: int = 0,
    auto_apply: AutoApplyPolicy = AutoApplyPolicy.NEVER,
    json_schema: dict | None = None,
    required_fields: list[str] | None = None,
    max_array_length: dict | None = None,
) -> FieldBinding:
    return FieldBinding(
        id=bid,
        artifact_type=artifact_type,
        field_path=field_path,
        scope=BindingScope.TYPE_DEFAULT,
        scope_id="*",
        prompt_asset_id="pa1",
        policy=BindingPolicy(
            locked=locked,
            cooldown_seconds=cooldown,
            auto_apply=auto_apply,
        ),
        output_contract=OutputContract(
            json_schema=json_schema or {},
            required_fields=required_fields or [],
            max_array_length=max_array_length or {},
        ),
    )


def _make_artifact(aid: str = "art1", atype: str = "user_story") -> ArtifactContext:
    return ArtifactContext(
        id=aid,
        type=atype,
        title="Test Story",
        body="As a user I can do something.",
    )


def _make_request(
    *,
    binding_id: str | None = "b1",
    field_path: str = "body",
    artifact_id: str = "art1",
    artifact_type: str = "user_story",
    run_id: str = "run-001",
) -> FieldRunRequest:
    return FieldRunRequest(
        artifact_id=artifact_id,
        artifact_type=artifact_type,
        field_path=field_path,
        binding_id=binding_id,
        run_id=run_id,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestFieldRunHappyPath:
    def test_returns_field_run_result(self):
        b = _make_binding()
        req = _make_request()
        result = run_field(req, bindings=[b], primary=_make_artifact())
        assert isinstance(result, FieldRunResult)

    def test_proposal_contains_field_path(self):
        b = _make_binding()
        req = _make_request()
        result = run_field(req, bindings=[b], primary=_make_artifact())
        assert isinstance(result, FieldRunResult)
        assert "body" in result.proposal

    def test_schema_valid_true(self):
        b = _make_binding()
        req = _make_request()
        result = run_field(req, bindings=[b], primary=_make_artifact())
        assert isinstance(result, FieldRunResult)
        assert result.schema_valid is True

    def test_cost_tokens_recorded(self):
        b = _make_binding()
        req = _make_request()
        result = run_field(req, bindings=[b], primary=_make_artifact())
        assert isinstance(result, FieldRunResult)
        assert result.cost_tokens > 0

    def test_trace_id_format(self):
        b = _make_binding()
        req = _make_request()
        result = run_field(req, bindings=[b], primary=_make_artifact())
        assert isinstance(result, FieldRunResult)
        assert result.trace_id.startswith("trace:")

    def test_bundle_hash_in_result(self):
        b = _make_binding()
        req = _make_request()
        result = run_field(req, bindings=[b], primary=_make_artifact())
        assert isinstance(result, FieldRunResult)
        assert result.bundle_hash.startswith("sha256:")

    def test_deterministic_proposal(self):
        """Same inputs → same proposal (via deterministic bundle hash)."""
        b = _make_binding()
        art = _make_artifact()
        r1 = run_field(_make_request(run_id="r1"), bindings=[b], primary=art)
        r2 = run_field(_make_request(run_id="r2"), bindings=[b], primary=art)
        assert isinstance(r1, FieldRunResult)
        assert isinstance(r2, FieldRunResult)
        # Same artifact → same bundle hash
        assert r1.bundle_hash == r2.bundle_hash
        # Same bundle hash → same proposal
        assert r1.proposal == r2.proposal

    def test_auto_apply_false_by_default(self):
        b = _make_binding(auto_apply=AutoApplyPolicy.NEVER)
        result = run_field(_make_request(), bindings=[b], primary=_make_artifact())
        assert isinstance(result, FieldRunResult)
        assert result.can_auto_apply is False

    def test_auto_apply_true_when_policy_allows(self):
        b = _make_binding(auto_apply=AutoApplyPolicy.LOW_RISK)
        result = run_field(_make_request(), bindings=[b], primary=_make_artifact())
        assert isinstance(result, FieldRunResult)
        assert result.can_auto_apply is True


class TestFieldRunLockAndCooldown:
    def test_locked_field_returns_error(self):
        b = _make_binding(locked=True)
        result = run_field(_make_request(), bindings=[b], primary=_make_artifact())
        assert isinstance(result, FieldRunError)
        assert result.code == "FIELD_LOCKED"

    def test_locked_error_contains_binding_id(self):
        b = _make_binding("lock-binding", locked=True)
        result = run_field(_make_request(binding_id="lock-binding"), bindings=[b], primary=_make_artifact())
        assert isinstance(result, FieldRunError)
        assert result.detail.get("binding_id") == "lock-binding"


class TestFieldRunBindingResolution:
    def test_binding_not_found_by_id(self):
        result = run_field(
            _make_request(binding_id="ghost"),
            bindings=[_make_binding("b1")],
            primary=_make_artifact(),
        )
        assert isinstance(result, FieldRunError)
        assert result.code == "BINDING_NOT_FOUND"

    def test_resolve_binding_when_id_is_none(self):
        b = _make_binding("auto-b", artifact_type="user_story", field_path="body")
        req = _make_request(binding_id=None, artifact_type="user_story", field_path="body")
        result = run_field(req, bindings=[b], primary=_make_artifact())
        assert isinstance(result, FieldRunResult)
        assert result.binding_id == "auto-b"

    def test_no_matching_binding_when_id_is_none(self):
        req = _make_request(binding_id=None, artifact_type="persona", field_path="body")
        result = run_field(req, bindings=[_make_binding()], primary=_make_artifact())
        assert isinstance(result, FieldRunError)
        assert result.code == "BINDING_NOT_FOUND"


class TestFieldRunSchemaValidation:
    def test_string_schema_enforced(self):
        b = _make_binding(json_schema={"type": "string"}, field_path="body")
        # body field returns a string from stub — should pass
        req = _make_request(field_path="body")
        result = run_field(req, bindings=[b], primary=_make_artifact())
        assert isinstance(result, FieldRunResult)
        assert result.schema_valid is True

    def test_array_schema_on_array_field(self):
        b = _make_binding(json_schema={"type": "array"}, field_path="items")
        req = _make_request(field_path="items")
        result = run_field(req, bindings=[b], primary=_make_artifact())
        assert isinstance(result, FieldRunResult)
        assert result.schema_valid is True

    def test_required_fields_violation(self):
        # Create a binding that requires a dict field "name" but the artifact
        # gets a plain string proposal → violation
        b = FieldBinding(
            id="b-strict",
            artifact_type="persona",
            field_path="body",
            scope=BindingScope.TYPE_DEFAULT,
            scope_id="*",
            prompt_asset_id="pa1",
            output_contract=OutputContract(
                json_schema={"type": "object"},
                required_fields=["name", "goal"],
            ),
        )
        req = FieldRunRequest(
            artifact_id="art1",
            artifact_type="persona",
            field_path="body",
            binding_id="b-strict",
            run_id="r-strict",
        )
        result = run_field(req, bindings=[b], primary=_make_artifact("art1", "persona"))
        # Stub returns a string for "body" on "persona", which fails "type: object"
        # AND required_fields — should get SCHEMA_VIOLATION
        assert isinstance(result, FieldRunError)
        assert result.code == "SCHEMA_VIOLATION"


class TestFieldRunWithContext:
    def test_accepts_parents_and_siblings(self):
        b = _make_binding()
        parent = ArtifactContext("par1", "epic", "Epic 1", "An epic")
        sibling = ArtifactContext("sib1", "user_story", "Story 2", "Another story")
        result = run_field(
            _make_request(),
            bindings=[b],
            primary=_make_artifact(),
            parents=[parent],
            siblings=[sibling],
        )
        assert isinstance(result, FieldRunResult)
