"""Tests for Mermaid parse/serialise/drift."""
from __future__ import annotations

import pytest
from backend.app.graph.mermaid import (
    MermaidEdge,
    MermaidGraph,
    MermaidNode,
    detect_drift,
    graph_to_mermaid,
    parse_mermaid,
)

# ---------------------------------------------------------------------------
# parse_mermaid
# ---------------------------------------------------------------------------

SIMPLE_FLOWCHART = """\
flowchart TD
    A[Start] --> B{Decide}
    B --> C[Yes]
    B --> D[No]
    C --> E[End]
    D --> E
"""

def test_parse_mermaid_node_count():
    g = parse_mermaid(SIMPLE_FLOWCHART)
    ids = {n.id for n in g.nodes}
    assert ids == {"A", "B", "C", "D", "E"}

def test_parse_mermaid_node_labels():
    g = parse_mermaid(SIMPLE_FLOWCHART)
    by_id = {n.id: n for n in g.nodes}
    assert by_id["A"].label == "Start"
    assert by_id["B"].label == "Decide"
    assert by_id["C"].label == "Yes"
    assert by_id["D"].label == "No"

def test_parse_mermaid_edge_count():
    g = parse_mermaid(SIMPLE_FLOWCHART)
    assert len(g.edges) == 5

def test_parse_mermaid_edges():
    g = parse_mermaid(SIMPLE_FLOWCHART)
    pairs = {(e.source, e.target) for e in g.edges}
    assert ("A", "B") in pairs
    assert ("B", "C") in pairs
    assert ("B", "D") in pairs
    assert ("C", "E") in pairs
    assert ("D", "E") in pairs

def test_parse_mermaid_graph_td():
    src = "graph TD\n    X --> Y\n    Y --> Z\n"
    g = parse_mermaid(src)
    assert {n.id for n in g.nodes} == {"X", "Y", "Z"}
    assert len(g.edges) == 2

def test_parse_mermaid_edge_labels():
    src = "graph LR\n    A --yes--> B\n    A --no--> C\n"
    g = parse_mermaid(src)
    by_pair = {(e.source, e.target): e.label for e in g.edges}
    assert by_pair[("A", "B")] == "yes"
    assert by_pair[("A", "C")] == "no"

def test_parse_mermaid_pipe_edge_labels():
    src = "graph TD\n    A -->|pass| B\n    A -->|fail| C\n"
    g = parse_mermaid(src)
    by_pair = {(e.source, e.target): e.label for e in g.edges}
    assert by_pair[("A", "B")] == "pass"
    assert by_pair[("A", "C")] == "fail"

def test_parse_mermaid_standalone_node():
    src = "graph TD\n    myNode[My Label]\n    myNode --> other\n"
    g = parse_mermaid(src)
    by_id = {n.id: n for n in g.nodes}
    assert by_id["myNode"].label == "My Label"


# ---------------------------------------------------------------------------
# graph_to_mermaid
# ---------------------------------------------------------------------------

def test_graph_to_mermaid_header():
    nodes = [MermaidNode(id="A", label="A")]
    edges: list[MermaidEdge] = []
    out = graph_to_mermaid(nodes, edges, direction="TD")
    assert out.startswith("graph TD")

def test_graph_to_mermaid_contains_nodes():
    nodes = [MermaidNode(id="X", label="X"), MermaidNode(id="Y", label="Step Y")]
    edges = [MermaidEdge(source="X", target="Y")]
    out = graph_to_mermaid(nodes, edges)
    assert "X" in out
    assert "Step Y" in out

def test_graph_to_mermaid_contains_edges():
    nodes = [MermaidNode(id="A", label="A"), MermaidNode(id="B", label="B")]
    edges = [MermaidEdge(source="A", target="B")]
    out = graph_to_mermaid(nodes, edges)
    assert "A --> B" in out

def test_graph_to_mermaid_edge_with_label():
    nodes = [MermaidNode(id="A", label="A"), MermaidNode(id="B", label="B")]
    edges = [MermaidEdge(source="A", target="B", label="ok")]
    out = graph_to_mermaid(nodes, edges)
    assert "|ok|" in out

def test_graph_to_mermaid_direction():
    nodes = [MermaidNode(id="A", label="A")]
    out = graph_to_mermaid(nodes, [], direction="LR")
    assert "graph LR" in out


# ---------------------------------------------------------------------------
# detect_drift
# ---------------------------------------------------------------------------

def _make_graph(node_ids: list[str], edge_pairs: list[tuple[str, str]]) -> MermaidGraph:
    nodes = [MermaidNode(id=i, label=i) for i in node_ids]
    edges = [MermaidEdge(source=s, target=t) for s, t in edge_pairs]
    return MermaidGraph(nodes=nodes, edges=edges)


def test_detect_drift_no_change():
    g = _make_graph(["A", "B"], [("A", "B")])
    report = detect_drift(g, g)
    assert not report.has_drift
    assert report.nodes_added == []
    assert report.nodes_removed == []
    assert report.edges_added == []
    assert report.edges_removed == []

def test_detect_drift_node_added():
    old = _make_graph(["A", "B"], [("A", "B")])
    new = _make_graph(["A", "B", "C"], [("A", "B")])
    report = detect_drift(old, new)
    assert report.has_drift
    assert "C" in report.nodes_added
    assert report.nodes_removed == []

def test_detect_drift_node_removed():
    old = _make_graph(["A", "B", "C"], [("A", "B")])
    new = _make_graph(["A", "B"], [("A", "B")])
    report = detect_drift(old, new)
    assert report.has_drift
    assert "C" in report.nodes_removed
    assert report.nodes_added == []

def test_detect_drift_edge_added():
    old = _make_graph(["A", "B", "C"], [("A", "B")])
    new = _make_graph(["A", "B", "C"], [("A", "B"), ("B", "C")])
    report = detect_drift(old, new)
    assert report.has_drift
    assert ("B", "C") in report.edges_added
    assert report.edges_removed == []

def test_detect_drift_edge_removed():
    old = _make_graph(["A", "B", "C"], [("A", "B"), ("B", "C")])
    new = _make_graph(["A", "B", "C"], [("A", "B")])
    report = detect_drift(old, new)
    assert report.has_drift
    assert ("B", "C") in report.edges_removed
    assert report.edges_added == []

def test_detect_drift_mixed():
    old = _make_graph(["A", "B"], [("A", "B")])
    new = _make_graph(["A", "C"], [("A", "C")])
    report = detect_drift(old, new)
    assert report.has_drift
    assert "C" in report.nodes_added
    assert "B" in report.nodes_removed
    assert ("A", "C") in report.edges_added
    assert ("A", "B") in report.edges_removed


# ---------------------------------------------------------------------------
# Round-trip: parse → serialise → parse → same graph
# ---------------------------------------------------------------------------

def _node_set(g: MermaidGraph) -> set[str]:
    return {n.id for n in g.nodes}

def _edge_set(g: MermaidGraph) -> set[tuple[str, str]]:
    return {(e.source, e.target) for e in g.edges}

def test_roundtrip_simple():
    original_src = """\
graph TD
    A[Alpha] --> B[Beta]
    B --> C[Gamma]
    A --> C
"""
    g1 = parse_mermaid(original_src)
    serialised = graph_to_mermaid(g1.nodes, g1.edges, direction="TD")
    g2 = parse_mermaid(serialised)
    assert _node_set(g1) == _node_set(g2)
    assert _edge_set(g1) == _edge_set(g2)

def test_roundtrip_with_edge_labels():
    original_src = """\
graph LR
    Start --> Decision
    Decision --yes--> Done
    Decision --no--> Start
"""
    g1 = parse_mermaid(original_src)
    serialised = graph_to_mermaid(g1.nodes, g1.edges, direction="LR")
    g2 = parse_mermaid(serialised)
    assert _node_set(g1) == _node_set(g2)
    assert _edge_set(g1) == _edge_set(g2)

def test_roundtrip_no_drift():
    src = """\
flowchart TD
    P[Prompt] --> LLM[Model]
    LLM --> Output
"""
    g1 = parse_mermaid(src)
    serialised = graph_to_mermaid(g1.nodes, g1.edges)
    g2 = parse_mermaid(serialised)
    report = detect_drift(g1, g2)
    assert not report.has_drift
