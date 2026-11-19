"""
Tests for TSK-047: Staleness detection on context change.

Acceptance: Upstream approved change marks dependent bindings stale with evidence.
"""
from __future__ import annotations

import pytest

from backend.app.bindings.assembler import ArtifactContext, ContextBundle, ContextSlice, assemble_context
from backend.app.bindings.models import BindingScope, ContextRule, FieldBinding
from backend.app.bindings.staleness import ContextIndex, StalenessReport, detect_stale_bindings


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_binding(bid: str, artifact_type: str, field_path: str) -> FieldBinding:
    return FieldBinding(
        id=bid,
        artifact_type=artifact_type,
        field_path=field_path,
        scope=BindingScope.TYPE_DEFAULT,
        scope_id="*",
        prompt_asset_id="pa1",
    )


def _make_bundle(
    binding_id: str,
    artifact_id: str,
    field_path: str,
    upstream_ids: list[str],
) -> ContextBundle:
    """Create a minimal ContextBundle with given upstream ids as slice sources."""
    slices = [
        ContextSlice(
            kind="artifact_body",
            source_id=artifact_id,
            content="primary",
            token_estimate=5,
        )
    ] + [
        ContextSlice(
            kind="parent",
            source_id=uid,
            content=f"upstream {uid}",
            token_estimate=5,
        )
        for uid in upstream_ids
    ]
    return ContextBundle(
        binding_id=binding_id,
        artifact_id=artifact_id,
        field_path=field_path,
        slices=slices,
        dropped=[],
        total_tokens=5 * (1 + len(upstream_ids)),
        bundle_hash="sha256:test",
    )


# ---------------------------------------------------------------------------
# ContextIndex tests
# ---------------------------------------------------------------------------

class TestContextIndex:
    def test_record_bundle_indexes_upstream(self):
        idx = ContextIndex()
        bundle = _make_bundle("b1", "art1", "body", ["par1", "sib1"])
        idx.record_bundle(bundle)
        upstream = idx.get_upstream("b1", "art1")
        assert "par1" in upstream
        assert "sib1" in upstream

    def test_primary_artifact_not_in_upstream(self):
        idx = ContextIndex()
        bundle = _make_bundle("b1", "art1", "body", ["par1"])
        idx.record_bundle(bundle)
        upstream = idx.get_upstream("b1", "art1")
        assert "art1" not in upstream   # primary not counted as upstream

    def test_get_upstream_empty_when_no_entry(self):
        idx = ContextIndex()
        assert idx.get_upstream("unknown", "art1") == set()

    def test_multiple_bundles_merged(self):
        idx = ContextIndex()
        b1 = _make_bundle("b1", "art1", "body", ["par1"])
        b2 = _make_bundle("b1", "art1", "body", ["par2"])
        idx.record_bundle(b1)
        idx.record_bundle(b2)
        upstream = idx.get_upstream("b1", "art1")
        assert "par1" in upstream
        assert "par2" in upstream

    def test_all_entries_returns_all(self):
        idx = ContextIndex()
        idx.record_bundle(_make_bundle("b1", "art1", "body", ["par1"]))
        idx.record_bundle(_make_bundle("b2", "art2", "body", ["par2"]))
        entries = idx.all_entries()
        assert len(entries) == 2


# ---------------------------------------------------------------------------
# detect_stale_bindings tests
# ---------------------------------------------------------------------------

class TestDetectStaleBindings:
    def test_no_changes_no_reports(self):
        idx = ContextIndex()
        idx.record_bundle(_make_bundle("b1", "art1", "body", ["par1"]))
        b1 = _make_binding("b1", "user_story", "body")
        reports = detect_stale_bindings(
            changed_upstream_ids=set(),
            binding_registry=[b1],
            context_index=idx,
        )
        assert reports == []

    def test_changed_upstream_produces_report(self):
        idx = ContextIndex()
        idx.record_bundle(_make_bundle("b1", "art1", "body", ["req1"]))
        b1 = _make_binding("b1", "user_story", "body")
        reports = detect_stale_bindings(
            changed_upstream_ids={"req1"},
            binding_registry=[b1],
            context_index=idx,
        )
        assert len(reports) == 1
        r = reports[0]
        assert r.binding_id == "b1"
        assert r.artifact_id == "art1"
        assert "req1" in r.stale_upstream_ids

    def test_report_contains_evidence(self):
        idx = ContextIndex()
        idx.record_bundle(_make_bundle("b1", "art1", "body", ["req1"]))
        b1 = _make_binding("b1", "user_story", "body")
        reports = detect_stale_bindings(
            changed_upstream_ids={"req1"},
            binding_registry=[b1],
            context_index=idx,
        )
        assert reports[0].evidence  # non-empty string

    def test_unrelated_change_no_report(self):
        idx = ContextIndex()
        idx.record_bundle(_make_bundle("b1", "art1", "body", ["req1"]))
        b1 = _make_binding("b1", "user_story", "body")
        reports = detect_stale_bindings(
            changed_upstream_ids={"other-artifact"},
            binding_registry=[b1],
            context_index=idx,
        )
        assert reports == []

    def test_multiple_stale_upstreams(self):
        idx = ContextIndex()
        idx.record_bundle(_make_bundle("b1", "art1", "body", ["req1", "per1", "brf1"]))
        b1 = _make_binding("b1", "user_story", "body")
        reports = detect_stale_bindings(
            changed_upstream_ids={"req1", "per1"},
            binding_registry=[b1],
            context_index=idx,
        )
        assert len(reports) == 1
        assert set(reports[0].stale_upstream_ids) == {"req1", "per1"}

    def test_multiple_bindings_multiple_reports(self):
        idx = ContextIndex()
        idx.record_bundle(_make_bundle("b1", "art1", "body", ["req1"]))
        idx.record_bundle(_make_bundle("b2", "art2", "body", ["req1"]))
        b1 = _make_binding("b1", "user_story", "body")
        b2 = _make_binding("b2", "persona", "body")
        reports = detect_stale_bindings(
            changed_upstream_ids={"req1"},
            binding_registry=[b1, b2],
            context_index=idx,
        )
        assert len(reports) == 2

    def test_field_path_from_binding_registry(self):
        idx = ContextIndex()
        idx.record_bundle(_make_bundle("b1", "art1", "payload.acceptance_criteria", ["req1"]))
        b1 = _make_binding("b1", "user_story", "payload.acceptance_criteria")
        reports = detect_stale_bindings(
            changed_upstream_ids={"req1"},
            binding_registry=[b1],
            context_index=idx,
        )
        assert reports[0].field_path == "payload.acceptance_criteria"

    def test_unknown_binding_id_uses_unknown_field_path(self):
        """If the binding_id in the index is not in the registry, field_path defaults to 'unknown'."""
        idx = ContextIndex()
        idx.record_bundle(_make_bundle("ghost-binding", "art1", "body", ["req1"]))
        reports = detect_stale_bindings(
            changed_upstream_ids={"req1"},
            binding_registry=[],
            context_index=idx,
        )
        assert len(reports) == 1
        assert reports[0].field_path == "unknown"
