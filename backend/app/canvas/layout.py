from __future__ import annotations

from math import ceil, floor, log2, sqrt
from typing import Any, Literal

AutoLayoutPolicy = Literal["free", "grid", "column", "tree"]


def auto_layout(
    items: list[dict[str, Any]], policy: AutoLayoutPolicy, gap: float = 32
) -> list[dict[str, Any]]:
    if gap < 0:
        raise ValueError("Layout gap must be nonnegative")
    ordered = sorted(items, key=lambda item: (int(item.get("z", 0)), str(item["projection_id"])))
    if policy == "free" or not ordered:
        return [dict(item) for item in ordered]
    cell_width = max(float(item["width"]) for item in ordered)
    cell_height = max(float(item["height"]) for item in ordered)
    if policy == "column":
        y = 0.0
        result = []
        for item in ordered:
            result.append({**item, "x": 0.0, "y": y})
            y += float(item["height"]) + gap
        return result
    if policy == "tree":
        result = []
        for index, item in enumerate(ordered):
            level = int(log2(index + 1))
            first_at_level = 2**level - 1
            position = index - first_at_level
            result.append(
                {
                    **item,
                    "x": (position - (2**level - 1) / 2) * (cell_width + gap),
                    "y": level * (cell_height + gap),
                }
            )
        return result
    columns = ceil(sqrt(len(ordered)))
    return [
        {
            **item,
            "x": (index % columns) * (cell_width + gap),
            "y": (index // columns) * (cell_height + gap),
        }
        for index, item in enumerate(ordered)
    ]


def snap_layout(items: list[dict[str, Any]], grid_size: float = 16) -> list[dict[str, Any]]:
    if grid_size <= 0:
        raise ValueError("Grid size must be positive")
    return [
        {
            **item,
            "x": floor(float(item["x"]) / grid_size + 0.5) * grid_size,
            "y": floor(float(item["y"]) / grid_size + 0.5) * grid_size,
        }
        for item in items
    ]
