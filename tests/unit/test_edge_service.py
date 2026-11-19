from __future__ import annotations

import pytest
from prompt_studio_api.contracts.registry import validate_edge_pair

from backend.app.graph.edges import creates_cycle


def test_edge_registry_enforces_pairs_and_rejects_derived_edges() -> None:
    validate_edge_pair("depends_on", "task", "component")

    with pytest.raises(ValueError, match="Source type idea"):
        validate_edge_pair("depends_on", "idea", "task")
    with pytest.raises(ValueError, match="derived"):
        validate_edge_pair("realized_by", "requirement", "component")


def test_cycle_detection_checks_path_back_to_source() -> None:
    edges = [("a", "b"), ("b", "c")]
    assert creates_cycle(edges, source_id="c", target_id="a")
    assert not creates_cycle(edges, source_id="a", target_id="c")
    assert creates_cycle([], source_id="same", target_id="same")
