"""
Tests for TSK-054: Approval tiers + single-use tokens.
Tests for TSK-055: Undo (compensating patch) + project restore.
Tests for TSK-056: Failure taxonomy + PartialResult.
"""
from __future__ import annotations

import pytest

# ============================================================================
# TSK-054: Approval tokens
# ============================================================================

from backend.app.patches.approval import (
    ApprovalToken,
    TokenAlreadyConsumedError,
    TokenExpiredError,
    TokenNotFoundError,
    TokenStore,
)


class FakeClock:
    def __init__(self, t: float = 0.0):
        self.t = t
    def __call__(self) -> float:
        return self.t
    def advance(self, s: float) -> None:
        self.t += s


class TestApprovalTokenStore:
    def test_issue_returns_string(self):
        store = TokenStore()
        tok = store.issue()
        assert isinstance(tok, str) and len(tok) > 10

    def test_is_valid_after_issue(self):
        store = TokenStore()
        tok = store.issue(ttl_seconds=60)
        assert store.is_valid(tok)

    def test_consume_succeeds(self):
        store = TokenStore()
        tok = store.issue(ttl_seconds=60)
        record = store.consume(tok)
        assert record.consumed is True

    def test_consume_twice_raises(self):
        store = TokenStore()
        tok = store.issue(ttl_seconds=60)
        store.consume(tok)
        with pytest.raises(TokenAlreadyConsumedError):
            store.consume(tok)

    def test_consume_unknown_raises(self):
        store = TokenStore()
        with pytest.raises(TokenNotFoundError):
            store.consume("ghost-token")

    def test_expired_token_raises(self):
        clock = FakeClock(0.0)
        store = TokenStore(_clock=clock)
        tok = store.issue(ttl_seconds=10.0)
        clock.advance(11.0)
        with pytest.raises(TokenExpiredError):
            store.consume(tok)

    def test_is_valid_false_after_consume(self):
        store = TokenStore()
        tok = store.issue(ttl_seconds=60)
        store.consume(tok)
        assert not store.is_valid(tok)

    def test_is_valid_false_after_expire(self):
        clock = FakeClock(0.0)
        store = TokenStore(_clock=clock)
        tok = store.issue(ttl_seconds=5.0)
        clock.advance(6.0)
        assert not store.is_valid(tok)

    def test_valid_tokens_excludes_expired(self):
        clock = FakeClock(0.0)
        store = TokenStore(_clock=clock)
        t1 = store.issue(ttl_seconds=100.0)
        t2 = store.issue(ttl_seconds=1.0)
        clock.advance(2.0)
        valid = store.valid_tokens()
        assert t1 in valid
        assert t2 not in valid

    def test_purge_expired_removes_only_expired(self):
        clock = FakeClock(0.0)
        store = TokenStore(_clock=clock)
        store.issue(ttl_seconds=1.0)
        t2 = store.issue(ttl_seconds=100.0)
        clock.advance(2.0)
        removed = store.purge_expired()
        assert removed == 1
        assert store.is_valid(t2) is True  # t2 has 100s TTL, only 2s elapsed


# ============================================================================
# TSK-055: Compensating patch (Undo)
# ============================================================================

from backend.app.patches.engine import OpKind, Patch, PatchOperation
from backend.app.patches.undo import ArtifactSnapshot, build_compensating_patch


def _make_update_patch(artifact_id: str, fields: dict) -> Patch:
    return Patch(
        patch_id="p1",
        project_id="proj1",
        operations=[
            PatchOperation(
                kind=OpKind.UPDATE_ARTIFACT,
                artifact_id=artifact_id,
                fields=fields,
                base_revision=3,
            )
        ],
        created_by="user1",
    )


class TestBuildCompensatingPatch:
    def test_undo_id_format(self):
        p = _make_update_patch("art1", {"body": "new"})
        snap = {"art1": ArtifactSnapshot("art1", "user_story", {"body": "old"}, revision=3)}
        undo = build_compensating_patch(p, snapshots_before=snap)
        assert undo.patch_id == "undo:p1"

    def test_undo_update_restores_prior_fields(self):
        p = _make_update_patch("art1", {"body": "new"})
        snap = {"art1": ArtifactSnapshot("art1", "user_story", {"body": "old"}, revision=3)}
        undo = build_compensating_patch(p, snapshots_before=snap)
        assert len(undo.operations) == 1
        op = undo.operations[0]
        assert op.kind == OpKind.UPDATE_ARTIFACT
        assert op.fields == {"body": "old"}

    def test_undo_create_generates_delete(self):
        p = Patch(
            patch_id="p2",
            project_id="proj1",
            operations=[
                PatchOperation(
                    kind=OpKind.CREATE_ARTIFACT,
                    artifact_id="tmp:new1",
                    artifact_type="user_story",
                    fields={"title": "New Story"},
                )
            ],
            created_by="user1",
            approval_tier=1,
        )
        # Snapshot records what the real_id resolved to
        snap = {"tmp:new1": ArtifactSnapshot("REAL001", "user_story", {}, revision=0, existed=False)}
        undo = build_compensating_patch(p, snapshots_before=snap)
        assert len(undo.operations) == 1
        assert undo.operations[0].kind == OpKind.DELETE_ARTIFACT
        assert undo.approval_tier == 2  # delete requires tier-2

    def test_undo_delete_generates_create(self):
        p = Patch(
            patch_id="p3",
            project_id="proj1",
            operations=[
                PatchOperation(
                    kind=OpKind.DELETE_ARTIFACT,
                    artifact_id="art1",
                )
            ],
            created_by="user1",
            approval_tier=2,
        )
        snap = {"art1": ArtifactSnapshot("art1", "user_story", {"title": "Restored"}, revision=5)}
        undo = build_compensating_patch(p, snapshots_before=snap)
        assert len(undo.operations) == 1
        op = undo.operations[0]
        assert op.kind == OpKind.CREATE_ARTIFACT
        assert op.artifact_type == "user_story"

    def test_undo_create_edge_generates_delete_edge(self):
        p = Patch(
            patch_id="p4",
            project_id="proj1",
            operations=[
                PatchOperation(
                    kind=OpKind.CREATE_EDGE,
                    source_id="art1",
                    target_id="art2",
                    edge_type="implements",
                    edge_id="edge1",
                )
            ],
            created_by="user1",
        )
        undo = build_compensating_patch(p, snapshots_before={})
        assert len(undo.operations) == 1
        assert undo.operations[0].kind == OpKind.DELETE_EDGE

    def test_layout_ops_skipped(self):
        p = Patch(
            patch_id="p5",
            project_id="proj1",
            operations=[
                PatchOperation(
                    kind=OpKind.UPDATE_LAYOUT,
                    projection_id="proj1",
                    position={"x": 10, "y": 20},
                )
            ],
            created_by="user1",
        )
        undo = build_compensating_patch(p, snapshots_before={})
        assert len(undo.operations) == 0  # layout ops skipped

    def test_operations_in_reverse_order(self):
        """Multi-op undo should reverse the order."""
        p = Patch(
            patch_id="p6",
            project_id="proj1",
            operations=[
                PatchOperation(kind=OpKind.UPDATE_ARTIFACT, artifact_id="art1",
                               fields={"body": "v2"}, base_revision=1),
                PatchOperation(kind=OpKind.UPDATE_ARTIFACT, artifact_id="art2",
                               fields={"body": "v2"}, base_revision=1),
            ],
            created_by="user1",
        )
        snap = {
            "art1": ArtifactSnapshot("art1", "user_story", {"body": "v1"}, revision=1),
            "art2": ArtifactSnapshot("art2", "user_story", {"body": "v1"}, revision=1),
        }
        undo = build_compensating_patch(p, snapshots_before=snap)
        assert len(undo.operations) == 2
        # Reversed: art2 first, art1 second
        assert undo.operations[0].artifact_id == "art2"
        assert undo.operations[1].artifact_id == "art1"

    def test_missing_snapshot_skips_op(self):
        """If no snapshot for an UPDATE, the op is skipped (can't restore what we don't know)."""
        p = _make_update_patch("art-no-snap", {"body": "new"})
        undo = build_compensating_patch(p, snapshots_before={})
        assert len(undo.operations) == 0


# ============================================================================
# TSK-056: Failure taxonomy + PartialResult
# ============================================================================

from backend.app.patches.taxonomy import (
    ERROR_DESCRIPTIONS,
    ErrorCode,
    OpStatus,
    PartialOpResult,
    PartialResult,
    validation_to_partial,
)
from backend.app.patches.engine import ValidationResult, OperationError


class TestErrorCodes:
    def test_all_codes_have_descriptions(self):
        for code in ErrorCode:
            assert code in ERROR_DESCRIPTIONS, f"Missing description for {code}"

    def test_stale_base_code_value(self):
        assert ErrorCode.STALE_BASE == "STALE_BASE"

    def test_field_locked_code_value(self):
        assert ErrorCode.FIELD_LOCKED == "FIELD_LOCKED"


class TestPartialResult:
    def test_counts(self):
        pr = PartialResult(
            patch_id="p1",
            overall_success=False,
            op_results=[
                PartialOpResult(0, OpStatus.OK),
                PartialOpResult(1, OpStatus.FAILED, code="STALE_BASE", message="stale"),
                PartialOpResult(2, OpStatus.OK),
            ],
        )
        assert pr.succeeded_count == 2
        assert pr.failed_count == 1

    def test_to_dict(self):
        pr = PartialResult(
            patch_id="p1",
            overall_success=True,
            op_results=[PartialOpResult(0, OpStatus.OK)],
        )
        d = pr.to_dict()
        assert d["patch_id"] == "p1"
        assert d["overall_success"] is True
        assert len(d["op_results"]) == 1


class TestValidationToPartial:
    def test_all_ok_when_valid(self):
        vr = ValidationResult(valid=True)
        pr = validation_to_partial(vr, "p1", total_ops=3)
        assert pr.overall_success is True
        assert all(r.status == OpStatus.OK for r in pr.op_results if r.operation_index >= 0)

    def test_failed_op_marked(self):
        vr = ValidationResult(valid=True)
        vr.add_error(1, "STALE_BASE", "stale", "base_revision")
        pr = validation_to_partial(vr, "p1", total_ops=3)
        assert pr.overall_success is False
        # Find the op_result for index 1
        r = next(r for r in pr.op_results if r.operation_index == 1)
        assert r.status == OpStatus.FAILED
        assert r.code == "STALE_BASE"

    def test_patch_level_error_included(self):
        vr = ValidationResult(valid=True)
        vr.add_error(-1, "PERM_DENIED", "viewer cannot patch")
        pr = validation_to_partial(vr, "p1", total_ops=2)
        assert pr.overall_success is False
        patch_level = [r for r in pr.op_results if r.operation_index == -1]
        assert len(patch_level) == 1
        assert patch_level[0].code == "PERM_DENIED"
