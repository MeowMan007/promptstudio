from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_excalidraw_imports_are_confined_to_canvas_package() -> None:
    source_roots = [ROOT / "apps", ROOT / "packages"]
    for source_root in source_roots:
        for path in source_root.rglob("*"):
            if not path.is_file() or path.suffix not in {".ts", ".tsx", ".js", ".jsx"}:
                continue
            if "packages/canvas/" in path.as_posix():
                continue
            assert "@excalidraw/" not in path.read_text(encoding="utf-8"), path
