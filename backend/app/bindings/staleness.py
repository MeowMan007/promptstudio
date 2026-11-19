"""
TSK-047: Staleness detection on context change.

When an upstream artifact changes (e.g., a Requirement is updated after a
User Story was written against it), any FieldBinding that depended on that
artifact via context slices may now be "stale" — its cached proposal no
longer reflects the current context.

This module provides:
  - StalenessReport: a detected staleness event
  - detect_stale_bindings(artifact_id, changed_upstream_ids, binding_registry,
                           context_index): → list[StalenessReport]
  - ContextIndex: lightweight index of (binding_id, artifact_id) → upstream ids used

The ContextIndex is populated from ContextBundles produced by the assembler
(TSK-041). It records which upstream artifact_ids appeared in the bundle's
slices for each (binding_id, primary_artifact_id) pair.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.app.bindings.assembler import ContextBundle, ContextSlice
from backend.app.bindings.models import FieldBinding


# ---------------------------------------------------------------------------
# Staleness report
# ---------------------------------------------------------------------------

@dataclass
class StalenessReport:
    """One detected staleness event."""
    binding_id: str
    artifact_id: str    # the artifact whose field may be stale
    field_path: str
    stale_upstream_ids: list[str]   # which upstream artifact ids changed
    evidence: str                   # human-readable explanation


# ---------------------------------------------------------------------------
# Context index
# ---------------------------------------------------------------------------

@dataclass
class ContextIndex:
    """
    Maps (binding_id, artifact_id) → set of upstream artifact_ids
    that appeared in the context bundle used to generate the last proposal.

    Call record_bundle() after each successful field run to keep it up to date.
    """
    _index: dict[tuple[str, str], set[str]] = field(default_factory=dict)

    def record_bundle(self, bundle: ContextBundle) -> None:
        """Index all source_ids from a bundle's slices as upstream context."""
        key = (bundle.binding_id, bundle.artifact_id)
        upstream: set[str] = set()
        for sl in bundle.slices:
            if sl.source_id and sl.source_id != bundle.artifact_id:
                upstream.add(sl.source_id)
        # Merge with existing (don't lose history)
        existing = self._index.get(key, set())
        self._index[key] = existing | upstream

    def get_upstream(self, binding_id: str, artifact_id: str) -> set[str]:
        """Return the set of upstream artifact_ids for this (binding, artifact) pair."""
        return self._index.get((binding_id, artifact_id), set())

    def all_entries(self) -> list[tuple[str, str, set[str]]]:
        """Return all (binding_id, artifact_id, upstream_ids) entries."""
        return [(bid, aid, ups) for (bid, aid), ups in self._index.items()]


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------

def detect_stale_bindings(
    *,
    changed_upstream_ids: set[str],
    binding_registry: list[FieldBinding],
    context_index: ContextIndex,
) -> list[StalenessReport]:
    """
    Detect which (binding_id, artifact_id) pairs are now stale given
    the set of upstream artifacts that just changed.

    A binding run is stale if at least one of the artifact_ids in its
    recorded context bundle appears in `changed_upstream_ids`.

    Parameters
    ----------
    changed_upstream_ids:
        IDs of artifacts that were modified in the latest patch/apply.
    binding_registry:
        All known FieldBindings (used to look up field_path).
    context_index:
        The ContextIndex populated from past runs.

    Returns
    -------
    List of StalenessReport, one per stale (binding_id, artifact_id) pair.
    """
    if not changed_upstream_ids:
        return []

    # Build a quick id → binding map
    binding_map: dict[str, FieldBinding] = {b.id: b for b in binding_registry}

    reports: list[StalenessReport] = []

    for binding_id, artifact_id, upstream_ids in context_index.all_entries():
        stale_ids = upstream_ids & changed_upstream_ids
        if not stale_ids:
            continue

        binding = binding_map.get(binding_id)
        field_path = binding.field_path if binding else "unknown"

        stale_list = sorted(stale_ids)
        evidence = (
            f"Artifact {artifact_id!r} field {field_path!r} was last generated using "
            f"context from {stale_list}; "
            f"those upstream artifacts have since been modified."
        )

        reports.append(StalenessReport(
            binding_id=binding_id,
            artifact_id=artifact_id,
            field_path=field_path,
            stale_upstream_ids=stale_list,
            evidence=evidence,
        ))

    return reports
