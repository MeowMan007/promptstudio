from __future__ import annotations

from collections.abc import Iterable


def creates_cycle(
    edges: Iterable[tuple[str, str]],
    *,
    source_id: str,
    target_id: str,
) -> bool:
    adjacency: dict[str, list[str]] = {}
    for edge_source, edge_target in edges:
        adjacency.setdefault(edge_source, []).append(edge_target)
    adjacency.setdefault(source_id, []).append(target_id)

    pending = [target_id]
    visited: set[str] = set()
    while pending:
        current = pending.pop()
        if current == source_id:
            return True
        if current in visited:
            continue
        visited.add(current)
        pending.extend(adjacency.get(current, ()))
    return False
