"""
Tests for TSK-040 (FieldBinding resolution) and TSK-041 (context assembler).
"""
from __future__ import annotations

import pytest

from backend.app.bindings.models import (
    AutoApplyPolicy,
    BindingPolicy,
    BindingScope,
    ContextRule,
    FieldBinding,
    OutputContract,
    resolve_binding,
)
from backend.app.bindings.assembler import (
    ArtifactContext,
    assemble_context,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_binding(
    *,
    scope: BindingScope = BindingScope.TYPE_DEFAULT,
    scope_id: str = "",
    artifact_type: str = "requirement",
    field_path: str = "body",
    prompt_asset_id: str = "pa-001",
    revision: int = 1,
    max_tokens: int = 8192,
    locked: bool = False,
) -> FieldBinding:
    return FieldBinding(
        id=f"b-{scope.value}-{revision}",
        artifact_type=artifact_type,
        field_path=field_path,
        scope=scope,
        scope_id=scope_id,
        prompt_asset_id=prompt_asset_id,
        context_rule=ContextRule(max_tokens=max_tokens),
        output_contract=OutputContract(),
        policy=BindingPolicy(locked=locked),
        revision=revision,
    )


def make_artifact(**kwargs: object) -> ArtifactContext:
    defaults = dict(id="art-1", type="requirement", title="Test", body="Body text", sensitivity=None)
    defaults.update(kwargs)  # type: ignore[arg-type]
    return ArtifactContext(**defaults)  # type: ignore[arg-type]


# ── resolve_binding ───────────────────────────────────────────────────────────

class TestResolveBinding:
    def test_returns_none_for_empty(self) -> None:
        assert resolve_binding([], "requirement", "body") is None

    def test_returns_type_default_when_no_narrower(self) -> None:
        b = make_binding(scope=BindingScope.TYPE_DEFAULT)
        result = resolve_binding([b], "requirement", "body")
        assert result is b

    def test_project_overrides_type_default(self) -> None:
        td = make_binding(scope=BindingScope.TYPE_DEFAULT)
        proj = make_binding(scope=BindingScope.PROJECT, scope_id="proj-1")
        result = resolve_binding([td, proj], "requirement", "body", project_id="proj-1")
        assert result is proj

    def test_artifact_overrides_project(self) -> None:
        proj = make_binding(scope=BindingScope.PROJECT, scope_id="proj-1")
        art = make_binding(scope=BindingScope.ARTIFACT, scope_id="art-1")
        result = resolve_binding(
            [proj, art], "requirement", "body",
            project_id="proj-1", artifact_id="art-1",
        )
        assert result is art

    def test_run_overrides_artifact(self) -> None:
        art = make_binding(scope=BindingScope.ARTIFACT, scope_id="art-1")
        run = make_binding(scope=BindingScope.RUN, scope_id="run-1")
        result = resolve_binding(
            [art, run], "requirement", "body",
            artifact_id="art-1", run_id="run-1",
        )
        assert result is run

    def test_ignores_wrong_artifact_type(self) -> None:
        b = make_binding(artifact_type="screen")
        assert resolve_binding([b], "requirement", "body") is None

    def test_ignores_wrong_field_path(self) -> None:
        b = make_binding(field_path="title")
        assert resolve_binding([b], "requirement", "body") is None

    def test_higher_revision_wins_on_tie(self) -> None:
        b1 = make_binding(scope=BindingScope.TYPE_DEFAULT, revision=1)
        b2 = make_binding(scope=BindingScope.TYPE_DEFAULT, revision=3)
        result = resolve_binding([b1, b2], "requirement", "body")
        assert result is b2

    def test_project_binding_not_applied_for_wrong_project(self) -> None:
        proj = make_binding(scope=BindingScope.PROJECT, scope_id="proj-X")
        result = resolve_binding([proj], "requirement", "body", project_id="proj-Y")
        assert result is None


# ── assemble_context ──────────────────────────────────────────────────────────

class TestAssembleContext:
    def test_bundle_contains_primary_body(self) -> None:
        binding = make_binding()
        artifact = make_artifact(body="Acceptance criteria here")
        bundle = assemble_context(binding=binding, primary=artifact)
        texts = " ".join(s.content for s in bundle.slices)
        assert "Acceptance criteria here" in texts

    def test_same_inputs_produce_same_hash(self) -> None:
        binding = make_binding()
        artifact = make_artifact()
        b1 = assemble_context(binding=binding, primary=artifact)
        b2 = assemble_context(binding=binding, primary=artifact)
        assert b1.bundle_hash == b2.bundle_hash

    def test_different_inputs_produce_different_hash(self) -> None:
        binding = make_binding()
        a1 = make_artifact(body="Content A")
        a2 = make_artifact(body="Content B")
        h1 = assemble_context(binding=binding, primary=a1).bundle_hash
        h2 = assemble_context(binding=binding, primary=a2).bundle_hash
        assert h1 != h2

    def test_budget_exceeded_items_go_to_dropped(self) -> None:
        binding = make_binding(max_tokens=5)   # very small budget
        # Primary body alone should exceed this tiny budget
        artifact = make_artifact(body="A" * 200)  # ~50 tokens
        bundle = assemble_context(binding=binding, primary=artifact)
        # Either slices or dropped should contain the content
        assert bundle.total_tokens <= 5 or len(bundle.dropped) > 0

    def test_sensitive_content_is_redacted(self) -> None:
        binding = make_binding()
        # sensitivity tag matches the redact list
        artifact = make_artifact(sensitivity="secret", body="Top secret plan")
        bundle = assemble_context(binding=binding, primary=artifact)
        body_slices = [s for s in bundle.slices if s.kind == "artifact_body"]
        assert all(s.redacted for s in body_slices)

    def test_parents_included_when_rule_set(self) -> None:
        binding = make_binding()
        artifact = make_artifact()
        parent = make_artifact(id="parent-1", title="Parent epic", body="Epic body")
        bundle = assemble_context(binding=binding, primary=artifact, parents=[parent])
        parent_slices = [s for s in bundle.slices if s.kind == "parent"]
        assert len(parent_slices) == 1
        assert "Parent epic" in parent_slices[0].content

    def test_jit_handles_appended(self) -> None:
        binding = make_binding()
        artifact = make_artifact()
        bundle = assemble_context(
            binding=binding, primary=artifact,
            jit_handles={"glossary": "term: definition"},
        )
        handle_slices = [s for s in bundle.slices if s.kind == "jit_handle"]
        assert len(handle_slices) == 1
        assert "glossary" in handle_slices[0].content

    def test_dropped_items_reported(self) -> None:
        binding = make_binding(max_tokens=20)
        artifact = make_artifact(body="Short")
        parent = make_artifact(id="p1", body="X" * 500)   # exceeds remaining budget
        bundle = assemble_context(binding=binding, primary=artifact, parents=[parent])
        assert any(d.source_id == "p1" for d in bundle.dropped)

    def test_bundle_hash_starts_with_sha256(self) -> None:
        binding = make_binding()
        artifact = make_artifact()
        bundle = assemble_context(binding=binding, primary=artifact)
        assert bundle.bundle_hash.startswith("sha256:")
