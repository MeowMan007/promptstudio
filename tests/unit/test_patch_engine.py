"""
Tests for TSK-050/051/052: Patch schema, validation, and apply.
"""
from __future__ import annotations

import pytest

from backend.app.patches.engine import (
    ApplyResult,
    OpKind,
    Patch,
    PatchOperation,
    ValidationResult,
    apply_patch,
    validate_patch,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_patch(
    *,
    operations: list[PatchOperation] | None = None,
    patch_id: str = "patch-001",
    approval_tier: int = 1,
    approval_token: str | None = None,
) -> Patch:
    return Patch(
        patch_id=patch_id,
        project_id="proj-1",
        operations=operations or [],
        created_by="user-1",
        approval_tier=approval_tier,
        approval_token=approval_token,
    )


def create_op(**kwargs: object) -> PatchOperation:
    defaults: dict = dict(kind=OpKind.CREATE_ARTIFACT, artifact_id="tmp:new-1", artifact_type="requirement", fields={"title": "New req"})
    defaults.update(kwargs)
    return PatchOperation(**defaults)


def update_op(**kwargs: object) -> PatchOperation:
    defaults: dict = dict(kind=OpKind.UPDATE_ARTIFACT, artifact_id="art-1", base_revision=1, fields={"title": "Updated"})
    defaults.update(kwargs)
    return PatchOperation(**defaults)


# ── validate_patch ────────────────────────────────────────────────────────────

class TestValidatePatch:
    def test_empty_patch_is_valid(self) -> None:
        result = validate_patch(make_patch())
        assert result.valid

    def test_viewer_cannot_patch(self) -> None:
        result = validate_patch(make_patch(operations=[create_op()]), caller_role="viewer")
        assert not result.valid
        assert any(e.code == "PERM_DENIED" for e in result.errors)

    def test_create_requires_tmp_id(self) -> None:
        op = create_op(artifact_id="real-not-tmp")
        result = validate_patch(make_patch(operations=[op]))
        assert not result.valid
        assert any(e.code == "INVALID_ID" for e in result.errors)

    def test_create_requires_title(self) -> None:
        op = create_op(fields={})  # no title
        result = validate_patch(make_patch(operations=[op]))
        assert not result.valid
        assert any(e.field == "title" for e in result.errors)

    def test_create_rejects_unknown_type(self) -> None:
        op = create_op(artifact_type="dragon")
        result = validate_patch(make_patch(operations=[op]))
        assert not result.valid
        assert any(e.code == "UNKNOWN_TYPE" for e in result.errors)

    def test_update_requires_base_revision(self) -> None:
        op = update_op(base_revision=None)
        result = validate_patch(
            make_patch(operations=[op]),
            existing_artifact_ids={"art-1"},
            existing_revision={"art-1": 1},
        )
        assert not result.valid
        assert any(e.field == "base_revision" for e in result.errors)

    def test_update_stale_base_rejected(self) -> None:
        op = update_op(base_revision=1)
        result = validate_patch(
            make_patch(operations=[op]),
            existing_artifact_ids={"art-1"},
            existing_revision={"art-1": 3},   # current is 3, patch says 1
        )
        assert not result.valid
        assert any(e.code == "STALE_BASE" for e in result.errors)

    def test_update_matching_revision_valid(self) -> None:
        op = update_op(base_revision=2)
        result = validate_patch(
            make_patch(operations=[op]),
            existing_artifact_ids={"art-1"},
            existing_revision={"art-1": 2},
        )
        assert result.valid

    def test_update_nonexistent_artifact_rejected(self) -> None:
        op = update_op(artifact_id="missing-id", base_revision=1)
        result = validate_patch(make_patch(operations=[op]), existing_artifact_ids=set())
        assert not result.valid
        assert any(e.code == "NOT_FOUND" for e in result.errors)

    def test_delete_requires_tier2(self) -> None:
        op = PatchOperation(kind=OpKind.DELETE_ARTIFACT, artifact_id="art-1")
        result = validate_patch(
            make_patch(operations=[op], approval_tier=1),
            existing_artifact_ids={"art-1"},
        )
        assert not result.valid
        assert any(e.code == "APPROVAL_REQUIRED" for e in result.errors)

    def test_create_edge_allows_tmp_endpoints(self) -> None:
        """Forward-reference: edge between two creates in same patch is valid."""
        create_a = create_op(artifact_id="tmp:A", fields={"title": "A"})
        create_b = create_op(artifact_id="tmp:B", artifact_type="task", fields={"title": "B"})
        edge_op = PatchOperation(kind=OpKind.CREATE_EDGE, source_id="tmp:A", target_id="tmp:B", edge_type="decomposes_to")
        result = validate_patch(make_patch(operations=[create_a, create_b, edge_op]))
        assert result.valid, [e.message for e in result.errors]

    def test_high_risk_tier2_requires_approval_token(self) -> None:
        patch = make_patch(approval_tier=2, approval_token=None)
        result = validate_patch(patch, approved_tokens={"tok-valid"})
        assert not result.valid
        assert any(e.code == "APPROVAL_REQUIRED" for e in result.errors)

    def test_tier2_with_valid_token_passes(self) -> None:
        patch = make_patch(approval_tier=2, approval_token="tok-valid")
        result = validate_patch(patch, approved_tokens={"tok-valid"})
        assert result.valid


# ── apply_patch ───────────────────────────────────────────────────────────────

class TestApplyPatch:
    def test_valid_create_succeeds(self) -> None:
        op = create_op()
        result = apply_patch(make_patch(operations=[op]))
        assert result.success
        assert "tmp:new-1" in result.id_map
        real_id = result.id_map["tmp:new-1"]
        assert len(real_id) == 26   # ULID-shaped

    def test_idempotent_second_apply(self) -> None:
        patch = make_patch(operations=[create_op()])
        r1 = apply_patch(patch)
        assert r1.success
        # Simulate second apply with same patch_id already in applied set
        r2 = apply_patch(patch, applied_patch_ids={patch.patch_id})
        assert r2.success   # idempotent — no error

    def test_invalid_patch_not_applied(self) -> None:
        op = create_op(artifact_id="bad-id-no-tmp")
        result = apply_patch(make_patch(operations=[op]))
        assert not result.success
        assert result.errors

    def test_update_bumps_revision(self) -> None:
        op = update_op(base_revision=1)
        result = apply_patch(
            make_patch(operations=[op]),
            existing_artifacts={"art-1": {"title": "Old"}},
            existing_revisions={"art-1": 1},
        )
        assert result.success
        assert result.new_revisions.get("art-1") == 2

    def test_stale_update_blocked(self) -> None:
        op = update_op(base_revision=1)
        result = apply_patch(
            make_patch(operations=[op]),
            existing_artifacts={"art-1": {"title": "Old"}},
            existing_revisions={"art-1": 5},   # stale
        )
        assert not result.success
        assert any(e.code == "STALE_BASE" for e in result.errors)
