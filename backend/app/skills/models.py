"""
TSK-060: Skill package storage + DB model + content hashing.

A skill package is a directory stored verbatim (content-addressed).
Key invariants:
  - Hash is computed over the entire directory tree (SHA-256 of sorted file paths + contents).
  - Once published (status=published), the content is immutable.
  - Metadata (name, version, description) must be declared in SKILL.md frontmatter.

Provides:
  - SkillPackage: the in-memory/DB model
  - hash_package_directory(path): → sha256 hex string
  - parse_skill_frontmatter(skill_md_text): → dict
  - SkillPackageStatus: draft | published | disabled
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Status enum
# ---------------------------------------------------------------------------

class SkillPackageStatus(str, Enum):
    DRAFT     = "draft"
    PUBLISHED = "published"
    DISABLED  = "disabled"


# ---------------------------------------------------------------------------
# DB model (in-memory representation; real impl uses SQLAlchemy)
# ---------------------------------------------------------------------------

@dataclass
class SkillPackage:
    """
    Represents a skill package stored verbatim.
    Maps to the skill_packages DB table (migration 0009_skills).
    """
    id: str                              # ULID
    name: str                            # from SKILL.md frontmatter
    version: str                         # semver string, e.g. "1.0.0"
    description: str
    content_hash: str                    # sha256:hex
    status: SkillPackageStatus = SkillPackageStatus.DRAFT
    trust_level: str = "untrusted"       # untrusted | community | official
    files: dict[str, str] = field(default_factory=dict)   # path → content
    metadata: dict[str, Any] = field(default_factory=dict)
    installed_by: str = "system"
    created_at: float = 0.0

    def is_mutable(self) -> bool:
        """Published packages are immutable."""
        return self.status != SkillPackageStatus.PUBLISHED

    def publish(self) -> None:
        """Transition to published (irreversible)."""
        self.status = SkillPackageStatus.PUBLISHED

    def disable(self) -> None:
        self.status = SkillPackageStatus.DISABLED


# ---------------------------------------------------------------------------
# Content hashing
# ---------------------------------------------------------------------------

def hash_package_directory(files: dict[str, str]) -> str:
    """
    Compute a deterministic SHA-256 hash over all file paths + contents.
    files: {relative_path: content_string}
    Returns: "sha256:<hex>"
    """
    h = hashlib.sha256()
    for path in sorted(files.keys()):
        # Hash path + content in a canonical format
        h.update(path.encode("utf-8"))
        h.update(b"\x00")
        h.update(files[path].encode("utf-8"))
        h.update(b"\xff")
    return f"sha256:{h.hexdigest()}"


def hash_package_path(directory: Path) -> str:
    """
    Compute hash from an actual directory on disk.
    Returns: "sha256:<hex>"
    """
    files: dict[str, str] = {}
    for p in sorted(directory.rglob("*")):
        if p.is_file():
            rel = str(p.relative_to(directory)).replace("\\", "/")
            try:
                files[rel] = p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                files[rel] = ""
    return hash_package_directory(files)


# ---------------------------------------------------------------------------
# SKILL.md frontmatter parser
# ---------------------------------------------------------------------------

_FRONTMATTER_RE = re.compile(
    r"^---\s*\n(?P<fm>.*?)^---\s*\n",
    re.MULTILINE | re.DOTALL,
)

_KV_RE = re.compile(r"^(?P<key>[a-zA-Z_][a-zA-Z0-9_-]*):\s*(?P<value>.+)\s*$", re.MULTILINE)


def parse_skill_frontmatter(skill_md_text: str) -> dict[str, str]:
    """
    Parse YAML-lite frontmatter from SKILL.md content.
    Only handles flat key: value pairs (no nested YAML).
    Returns dict of {key: value_string}.
    """
    m = _FRONTMATTER_RE.match(skill_md_text)
    if not m:
        return {}
    fm = m.group("fm")
    return {kv.group("key"): kv.group("value").strip() for kv in _KV_RE.finditer(fm)}
