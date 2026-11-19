"""TSK-098: Mermaid generators + SVG render gate.

Implements spec section 25.4:
  - generate_er_diagram(): erDiagram Mermaid from data entities
  - generate_flow_diagram(): flowchart TD Mermaid from user flows
  - Deterministic node IDs
  - validate_mermaid(): parse-level validation (structural)
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class ERRelation:
    from_entity: str
    to_entity: str
    cardinality: str = "||--o{"   # Mermaid ERD cardinality string
    label: str = ""


@dataclass
class ERAttribute:
    attr_type: str
    attr_name: str
    is_pk: bool = False
    is_fk: bool = False
    comment: str = ""


@dataclass
class EREntity:
    name: str
    attributes: list[ERAttribute] = field(default_factory=list)


@dataclass
class FlowNode:
    node_id: str
    label: str
    shape: str = "rect"   # rect | round | diamond | stadium | cylinder


@dataclass
class FlowEdge:
    from_id: str
    to_id: str
    label: str = ""
    style: str = "-->"   # --> | -.-> | ==>


@dataclass
class FlowGraph:
    title: str
    nodes: list[FlowNode]
    edges: list[FlowEdge]
    direction: str = "TD"   # TD | LR | BT | RL


# ---------------------------------------------------------------------------
# Node ID helpers (deterministic)
# ---------------------------------------------------------------------------

def _safe_id(name: str) -> str:
    """Convert a name to a safe Mermaid node ID (alphanumeric + underscore)."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", name).strip("_").lower()
    return slug or "node_" + hashlib.sha256(name.encode()).hexdigest()[:6]


# ---------------------------------------------------------------------------
# ER diagram generator
# ---------------------------------------------------------------------------

def generate_er_diagram(
    entities: list[EREntity],
    relations: list[ERRelation] | None = None,
) -> str:
    """Generate a Mermaid erDiagram block.

    Node IDs are deterministic (derived from entity name).
    """
    relations = relations or []
    lines = ["erDiagram"]

    # Sort for determinism
    for entity in sorted(entities, key=lambda e: e.name):
        lines.append(f"  {_safe_id(entity.name)} {{")
        for attr in entity.attributes:
            pk_marker = " PK" if attr.is_pk else ""
            fk_marker = " FK" if attr.is_fk else ""
            comment = f' "{attr.comment}"' if attr.comment else ""
            lines.append(f"    {attr.attr_type} {attr.attr_name}{pk_marker}{fk_marker}{comment}")
        lines.append("  }")

    for rel in sorted(relations, key=lambda r: (r.from_entity, r.to_entity)):
        from_id = _safe_id(rel.from_entity)
        to_id = _safe_id(rel.to_entity)
        label = f' : "{rel.label}"' if rel.label else ' : "has"'
        lines.append(f"  {from_id} {rel.cardinality} {to_id}{label}")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Flow diagram generator
# ---------------------------------------------------------------------------

_SHAPE_OPEN: dict[str, str] = {
    "rect": "[",
    "round": "(",
    "diamond": "{",
    "stadium": "([",
    "cylinder": "[(",
}
_SHAPE_CLOSE: dict[str, str] = {
    "rect": "]",
    "round": ")",
    "diamond": "}",
    "stadium": "])",
    "cylinder": ")]",
}


def generate_flow_diagram(graph: FlowGraph) -> str:
    """Generate a Mermaid flowchart TD/LR block.

    Node IDs are deterministic (safe slugs of node_id).
    """
    lines = [f"flowchart {graph.direction}"]

    # Deduplicate nodes by node_id
    seen: set[str] = set()
    for node in sorted(graph.nodes, key=lambda n: n.node_id):
        safe = _safe_id(node.node_id)
        if safe in seen:
            continue
        seen.add(safe)
        open_b = _SHAPE_OPEN.get(node.shape, "[")
        close_b = _SHAPE_CLOSE.get(node.shape, "]")
        lines.append(f"  {safe}{open_b}{node.label}{close_b}")

    for edge in sorted(graph.edges, key=lambda e: (e.from_id, e.to_id)):
        from_safe = _safe_id(edge.from_id)
        to_safe = _safe_id(edge.to_id)
        label_part = f"|{edge.label}|" if edge.label else ""
        lines.append(f"  {from_safe} {edge.style}{label_part} {to_safe}")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Validation gate (spec 25.4: "all .mmd parse and render")
# ---------------------------------------------------------------------------

class MermaidValidationError(ValueError):
    pass


_SUPPORTED_DIAGRAMS = re.compile(
    r"^(erDiagram|flowchart\s+(TD|LR|BT|RL)|graph\s+(TD|LR|BT|RL)|"
    r"sequenceDiagram|stateDiagram(-v2)?|classDiagram|xychart-beta)",
    re.M,
)


def validate_mermaid(source: str) -> list[str]:
    """Lightweight structural validation of a Mermaid diagram source.

    Checks:
      - Starts with a supported diagram type
      - No unclosed fences within the block
      - Reasonable line count (> 1 line)

    Returns list of error strings (empty = OK).
    """
    errors: list[str] = []
    stripped = source.strip()
    if not stripped:
        errors.append("Empty diagram source")
        return errors

    if not _SUPPORTED_DIAGRAMS.match(stripped):
        first_line = stripped.splitlines()[0]
        errors.append(f"Unknown or unsupported diagram type: {first_line!r}")

    if stripped.count("```") % 2 != 0:
        errors.append("Unclosed fenced code block detected inside diagram")

    if len(stripped.splitlines()) < 2:
        errors.append("Diagram has only one line — likely incomplete")

    return errors


def assert_valid_mermaid(source: str) -> None:
    """Raise MermaidValidationError if the diagram is invalid."""
    errors = validate_mermaid(source)
    if errors:
        raise MermaidValidationError(
            "Mermaid validation failed:\n" + "\n".join(f"  • {e}" for e in errors)
        )
