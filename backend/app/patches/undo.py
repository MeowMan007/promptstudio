"""
TSK-055: Undo (compensating patch) + project restore.

A compensating patch inverts a previously-applied patch by:
  - Converting UPDATE_ARTIFACT ops → UPDATE_ARTIFACT ops that restore prior field values
  - Converting CREATE_ARTIFACT ops → DELETE_ARTIFACT ops (tier-2, since deletes are risky)
  - Converting DELETE_ARTIFACT ops → CREATE_ARTIFACT ops (restoring from snapshot)
  - Converting CREATE_EDGE / DELETE_EDGE ops ↔ inverted
  - Skipping UPDATE_LAYOUT ops (layout undo is a separate concern)

Invariants:
  - The undo is itself a Patch that goes through the same validate+apply pipeline.
  - Every undo is audited (patch_id = f"undo:{original_patch_id}").
  - Layout undo (UPDATE_LAYOUT) is kept separate — visual position revert
    is a separate lower-risk operation.

Provides:
  - build_compensating_patch(original_patch, snapshot_before): → Patch
  - ArtifactSnapshot: before-state captured at apply time
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.app.patches.engine import (
    OpKind,
    Patch,
    PatchOperation,
)


# ---------------------------------------------------------------------------
# Snapshot: state captured before a patch was applied
# ---------------------------------------------------------------------------

@dataclass
class ArtifactSnapshot:
    """
    Captures the state of an artifact immediately before a patch was applied.
    Used by the undo builder to reconstruct compensating operations.
    """
    artifact_id: str
    artifact_type: str
    fields: dict[str, Any]       # field values BEFORE the patch
    revision: int                 # revision BEFORE the patch
    existed: bool = True          # False if the artifact was created by this patch


# ---------------------------------------------------------------------------
# Compensating patch builder
# ---------------------------------------------------------------------------

def build_compensating_patch(
    original_patch: Patch,
    *,
    snapshots_before: dict[str, ArtifactSnapshot],
    caller: str = "system",
) -> Patch:
    """
    Build a Patch that undoes the effects of `original_patch`.

    Parameters
    ----------
    original_patch:
        The patch that was successfully applied.
    snapshots_before:
        Map of artifact_id → ArtifactSnapshot captured immediately before
        the original patch was applied.
    caller:
        User / system identity that is performing the undo.

    Returns
    -------
    A new Patch with:
      - patch_id = f"undo:{original_patch.patch_id}"
      - Compensating operations in reverse order
      - approval_tier=2 if any DELETE_ARTIFACT ops are generated
    """
    comp_ops: list[PatchOperation] = []
    needs_tier2 = False

    # Process in reverse order so dependencies are correct
    for op in reversed(original_patch.operations):

        if op.kind == OpKind.UPDATE_ARTIFACT and op.artifact_id:
            snap = snapshots_before.get(op.artifact_id)
            if snap is not None:
                # Restore previous field values
                comp_ops.append(PatchOperation(
                    kind=OpKind.UPDATE_ARTIFACT,
                    artifact_id=op.artifact_id,
                    fields=snap.fields,
                    base_revision=snap.revision + 1,  # current rev = snap.revision + 1 (after apply)
                ))

        elif op.kind == OpKind.CREATE_ARTIFACT:
            # Undo a create → delete the new artifact (tier-2 required)
            # The real_id is in the patch's id_map (not stored here, so use op.artifact_id as placeholder)
            if op.artifact_id:
                # We need the real resolved id; callers should pass the actual id in snapshots_before
                snap = snapshots_before.get(op.artifact_id)
                real_id = snap.artifact_id if snap else op.artifact_id
                needs_tier2 = True
                comp_ops.append(PatchOperation(
                    kind=OpKind.DELETE_ARTIFACT,
                    artifact_id=real_id,
                ))

        elif op.kind == OpKind.DELETE_ARTIFACT and op.artifact_id:
            snap = snapshots_before.get(op.artifact_id)
            if snap is not None:
                # Restore deleted artifact (re-create with original fields)
                comp_ops.append(PatchOperation(
                    kind=OpKind.CREATE_ARTIFACT,
                    artifact_id=f"tmp:restore:{op.artifact_id[:20]}",
                    artifact_type=snap.artifact_type,
                    fields={**snap.fields, "id": snap.artifact_id},
                ))

        elif op.kind == OpKind.CREATE_EDGE:
            # Undo create edge → delete it
            comp_ops.append(PatchOperation(
                kind=OpKind.DELETE_EDGE,
                edge_id=op.edge_id or f"edge:{op.source_id}:{op.target_id}:{op.edge_type}",
            ))

        elif op.kind == OpKind.DELETE_EDGE and op.edge_id:
            # Undo delete edge → re-create (from snapshot info if available)
            snap = snapshots_before.get(op.edge_id)
            if snap is not None:
                comp_ops.append(PatchOperation(
                    kind=OpKind.CREATE_EDGE,
                    source_id=snap.fields.get("source_id", ""),
                    target_id=snap.fields.get("target_id", ""),
                    edge_type=snap.fields.get("edge_type", ""),
                    edge_id=op.edge_id,
                ))

        # UPDATE_LAYOUT: skip — layout undo is handled separately

    return Patch(
        patch_id=f"undo:{original_patch.patch_id}",
        project_id=original_patch.project_id,
        operations=comp_ops,
        created_by=caller,
        approval_tier=2 if needs_tier2 else 1,
        description=f"Undo patch {original_patch.patch_id!r} by {caller}",
    )
