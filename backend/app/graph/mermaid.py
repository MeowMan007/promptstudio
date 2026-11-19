"""Mermaid diagram round-trip and drift detection."""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class MermaidNode:
    id: str
    label: str


@dataclass(frozen=True)
class MermaidEdge:
    source: str
    target: str
    label: str | None = None


@dataclass
class MermaidGraph:
    nodes: list[MermaidNode]
    edges: list[MermaidEdge]


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

# Matches: graph TD / LR / TB / RL / BT  or  flowchart TD / LR / ...
_HEADER_RE = re.compile(
    r"^\s*(?:graph|flowchart)\s+(?:TD|LR|TB|RL|BT)\s*$",
    re.IGNORECASE,
)

# Node declaration patterns (without an edge):  id[label]  id{label}  id(label)  id((label))
_NODE_DECL_RE = re.compile(
    r"""^\s*
        (?P<id>[A-Za-z0-9_\-]+)         # node id
        (?:
            \[\[(?P<dl>[^\]]*)\]\]       # [[double bracket]]
          | \[(?P<sq>[^\]]*)\]           # [square]
          | \{(?P<cu>[^}]*)\}            # {curly}
          | \(\((?P<dc>[^)]*)\)\)        # ((double paren))
          | \((?P<pa>[^)]*)\)            # (paren)
          | >(?P<as>[^]]*)\]             # >asymmetric]
        )
        \s*$""",
    re.VERBOSE,
)

# Edge line:  src --> dst   or   src --label--> dst   or   src -- label --> dst
# Also handles  src -->|label| dst
_EDGE_RE = re.compile(
    r"""^\s*
        (?P<src>[A-Za-z0-9_\-]+)        # source id (bare)
        (?:\s*                           # optional source label (ignored for id)
            (?:\[\[[^\]]*\]\]|\[[^\]]*\]|\{[^}]*\}|\(\([^)]*\)\)|\([^)]*\)|>[^\]]*\])
        )?
        \s*
        (?:
            --(?P<lbl1>[^->]*)-->        # --text-->
          | -->?\|(?P<lbl2>[^|]*)\|      # -->|label|
          | -->                          # plain -->
          | ---(?P<lbl3>[^->]*)->        # ---text->  (single-headed)
          | ->                           # single arrow
        )
        \s*
        (?P<dst>[A-Za-z0-9_\-]+)        # target id (bare)
        (?:\s*                           # optional target label (ignored for id)
            (?:\[\[[^\]]*\]\]|\[[^\]]*\]|\{[^}]*\}|\(\([^)]*\)\)|\([^)]*\)|>[^\]]*\])
        )?
        \s*$""",
    re.VERBOSE,
)

# Combined edge+node label on the target side — capture target label
_EDGE_WITH_LABELS_RE = re.compile(
    r"""^\s*
        (?P<src_id>[A-Za-z0-9_\-]+)
        (?P<src_lbl>
            (?:\[\[[^\]]*\]\]|\[[^\]]*\]|\{[^}]*\}|\(\([^)]*\)\)|\([^)]*\)|>[^\]]*\])
        )?
        \s*
        (?:
            --(?P<lbl1>[^->]*)-->
          | -->?\|(?P<lbl2>[^|]*)\|
          | -->
          | ---(?P<lbl3>[^->]*)->
          | ->
        )
        \s*
        (?P<dst_id>[A-Za-z0-9_\-]+)
        (?P<dst_lbl>
            (?:\[\[[^\]]*\]\]|\[[^\]]*\]|\{[^}]*\}|\(\([^)]*\)\)|\([^)]*\)|>[^\]]*\])
        )?
        \s*$""",
    re.VERBOSE,
)


def _extract_label(raw: str) -> str:
    """Strip surrounding bracket characters and return inner text."""
    raw = raw.strip()
    for open_, close in [("[[", "]]"), ("((", "))"), ("[", "]"), ("{", "}"), ("(", ")"), (">", "]")]:
        if raw.startswith(open_) and raw.endswith(close):
            return raw[len(open_):-len(close)].strip()
    return raw


def parse_mermaid(source: str) -> MermaidGraph:
    """Parse a flowchart/graph Mermaid diagram into nodes and edges.

    Supports: graph TD/LR/TB, flowchart TD/LR, node labels with [] {} (),
    arrows --> and --text-->.
    """
    nodes: dict[str, MermaidNode] = {}
    edges: list[MermaidEdge] = []

    def ensure_node(node_id: str, label: str | None = None) -> None:
        if node_id not in nodes:
            nodes[node_id] = MermaidNode(id=node_id, label=label or node_id)
        elif label and nodes[node_id].label == node_id:
            # upgrade bare id to labelled node
            nodes[node_id] = MermaidNode(id=node_id, label=label)

    for raw_line in source.splitlines():
        line = raw_line.strip()
        # Skip blank lines, comments, and header
        if not line or line.startswith("%%") or _HEADER_RE.match(line):
            continue
        # Skip subgraph / end
        if line.lower().startswith("subgraph") or line.lower() == "end":
            continue
        # Try edge match first (more specific)
        m = _EDGE_WITH_LABELS_RE.match(line)
        if m:
            src_id = m.group("src_id")
            dst_id = m.group("dst_id")
            src_lbl_raw = m.group("src_lbl") or ""
            dst_lbl_raw = m.group("dst_lbl") or ""
            # edge label (first non-None of lbl1/lbl2/lbl3)
            edge_lbl = m.group("lbl1") or m.group("lbl2") or m.group("lbl3")
            if edge_lbl is not None:
                edge_lbl = edge_lbl.strip() or None

            ensure_node(src_id, _extract_label(src_lbl_raw) if src_lbl_raw else None)
            ensure_node(dst_id, _extract_label(dst_lbl_raw) if dst_lbl_raw else None)
            edges.append(MermaidEdge(source=src_id, target=dst_id, label=edge_lbl))
            continue

        # Try standalone node declaration
        m = _NODE_DECL_RE.match(line)
        if m:
            node_id = m.group("id")
            label_raw = (
                m.group("dl") or m.group("sq") or m.group("cu")
                or m.group("dc") or m.group("pa") or m.group("as")
                or node_id
            )
            ensure_node(node_id, label_raw.strip())

    return MermaidGraph(nodes=list(nodes.values()), edges=edges)


# ---------------------------------------------------------------------------
# Serialisation
# ---------------------------------------------------------------------------

def _node_mermaid(node: MermaidNode) -> str:
    """Render a single node as Mermaid.  Use [label] form."""
    if node.label == node.id:
        return node.id
    # Escape brackets in label
    safe_label = node.label.replace("[", "(").replace("]", ")")
    return f'{node.id}["{safe_label}"]'


def graph_to_mermaid(
    nodes: list[MermaidNode],
    edges: list[MermaidEdge],
    direction: str = "TD",
) -> str:
    """Serialise a graph back to Mermaid source."""
    lines: list[str] = [f"graph {direction}"]
    # Emit node declarations for all nodes
    for node in nodes:
        lines.append(f"    {_node_mermaid(node)}")
    # Emit edges
    for edge in edges:
        if edge.label:
            safe_lbl = edge.label.replace("|", "/")
            lines.append(f"    {edge.source} -->|{safe_lbl}| {edge.target}")
        else:
            lines.append(f"    {edge.source} --> {edge.target}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Drift detection
# ---------------------------------------------------------------------------

@dataclass
class DriftReport:
    nodes_added: list[str]       # ids in new but not old
    nodes_removed: list[str]     # ids in old but not new
    edges_added: list[tuple[str, str]]
    edges_removed: list[tuple[str, str]]
    has_drift: bool


def detect_drift(canonical: MermaidGraph, edited: MermaidGraph) -> DriftReport:
    """Compare two parsed graphs and return a drift report."""
    old_node_ids = {n.id for n in canonical.nodes}
    new_node_ids = {n.id for n in edited.nodes}

    nodes_added = sorted(new_node_ids - old_node_ids)
    nodes_removed = sorted(old_node_ids - new_node_ids)

    old_edges = {(e.source, e.target) for e in canonical.edges}
    new_edges = {(e.source, e.target) for e in edited.edges}

    edges_added = sorted(new_edges - old_edges)
    edges_removed = sorted(old_edges - new_edges)

    has_drift = bool(nodes_added or nodes_removed or edges_added or edges_removed)

    return DriftReport(
        nodes_added=nodes_added,
        nodes_removed=nodes_removed,
        edges_added=edges_added,
        edges_removed=edges_removed,
        has_drift=has_drift,
    )
