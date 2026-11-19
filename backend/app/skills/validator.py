"""
TSK-061: Skill validator — SK-VAL-01 through SK-VAL-10.

Ten validation rules applied before a skill package can be installed.
Each check is independent and returns a ValidationFailure on reject.

Rules:
  SK-VAL-01: SKILL.md must exist at the package root
  SK-VAL-02: name field must be non-empty, slug-safe [a-z0-9-_]+
  SK-VAL-03: version field must be a valid semver (major.minor.patch)
  SK-VAL-04: description field must be non-empty
  SK-VAL-05: No path traversal (.. segments) in any file path
  SK-VAL-06: No absolute paths in file listing
  SK-VAL-07: declared_tools list (if present) must only reference allowed tool names
  SK-VAL-08: Total package size must not exceed MAX_PACKAGE_BYTES
  SK-VAL-09: No binary files (only text; binary content rejected)
  SK-VAL-10: No secrets/credentials (heuristic: common secret patterns in content)

Acceptance (TSK-061): Each check has a test; invalid names/paths/tools rejected with exact reason.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from backend.app.skills.models import parse_skill_frontmatter


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_PACKAGE_BYTES = 10 * 1024 * 1024    # 10 MB

_VALID_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9\-_]{0,63}$")
_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")

_ALLOWED_TOOLS = frozenset({
    "read_file", "write_file", "run_command", "search_web",
    "read_artifact", "propose_patch", "assemble_context",
    "run_field", "get_binding", "query_graph",
})

# Secret heuristics: patterns that look like credentials
_SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_\-]?key|secret|password|token|private[_\-]?key)\s*[:=]\s*['\"]?[A-Za-z0-9+/\-_]{16,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),           # OpenAI key pattern
    re.compile(r"ghp_[A-Za-z0-9]{30,}"),           # GitHub PAT
    re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----"),
]

_BINARY_EXTS = frozenset({
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp",
    ".pdf", ".exe", ".dll", ".so", ".pyc", ".zip", ".tar", ".gz",
})


# ---------------------------------------------------------------------------
# Failure type
# ---------------------------------------------------------------------------

@dataclass
class ValidationFailure:
    rule: str           # e.g. "SK-VAL-02"
    reason: str         # human-readable rejection reason
    file_path: str | None = None   # which file triggered the failure


# ---------------------------------------------------------------------------
# Individual rule checkers
# ---------------------------------------------------------------------------

def _val_01_skill_md_exists(files: dict[str, str]) -> ValidationFailure | None:
    """SK-VAL-01: SKILL.md must exist at package root."""
    if "SKILL.md" not in files:
        return ValidationFailure("SK-VAL-01", "SKILL.md not found at package root")
    return None


def _val_02_valid_name(files: dict[str, str]) -> ValidationFailure | None:
    """SK-VAL-02: name must be non-empty and slug-safe."""
    skill_md = files.get("SKILL.md", "")
    fm = parse_skill_frontmatter(skill_md)
    name = fm.get("name", "").strip()
    if not name:
        return ValidationFailure("SK-VAL-02", "SKILL.md frontmatter missing 'name' field")
    if not _VALID_NAME_RE.match(name):
        return ValidationFailure(
            "SK-VAL-02",
            f"name {name!r} is invalid; must match [a-z0-9][a-z0-9\\-_]{{0,63}}",
        )
    return None


def _val_03_valid_version(files: dict[str, str]) -> ValidationFailure | None:
    """SK-VAL-03: version must be a valid semver."""
    skill_md = files.get("SKILL.md", "")
    fm = parse_skill_frontmatter(skill_md)
    version = fm.get("version", "").strip()
    if not version:
        return ValidationFailure("SK-VAL-03", "SKILL.md frontmatter missing 'version' field")
    if not _SEMVER_RE.match(version):
        return ValidationFailure(
            "SK-VAL-03",
            f"version {version!r} is not valid semver (major.minor.patch)",
        )
    return None


def _val_04_has_description(files: dict[str, str]) -> ValidationFailure | None:
    """SK-VAL-04: description must be non-empty."""
    skill_md = files.get("SKILL.md", "")
    fm = parse_skill_frontmatter(skill_md)
    desc = fm.get("description", "").strip()
    if not desc:
        return ValidationFailure("SK-VAL-04", "SKILL.md frontmatter missing 'description' field")
    return None


def _val_05_no_path_traversal(files: dict[str, str]) -> ValidationFailure | None:
    """SK-VAL-05: No path traversal (.. segments)."""
    for path in files:
        parts = path.replace("\\", "/").split("/")
        if ".." in parts:
            return ValidationFailure("SK-VAL-05", f"Path traversal detected: {path!r}", path)
    return None


def _val_06_no_absolute_paths(files: dict[str, str]) -> ValidationFailure | None:
    """SK-VAL-06: No absolute paths in file listing."""
    for path in files:
        norm = path.replace("\\", "/")
        if norm.startswith("/") or (len(norm) >= 2 and norm[1] == ":"):
            return ValidationFailure("SK-VAL-06", f"Absolute path not allowed: {path!r}", path)
    return None


def _val_07_allowed_tools(files: dict[str, str]) -> ValidationFailure | None:
    """SK-VAL-07: declared_tools must only reference allowed tool names."""
    skill_md = files.get("SKILL.md", "")
    fm = parse_skill_frontmatter(skill_md)
    tools_raw = fm.get("tools", "").strip()
    if not tools_raw:
        return None
    # Tools declared as comma-separated string in frontmatter
    declared = {t.strip() for t in tools_raw.split(",") if t.strip()}
    unknown = declared - _ALLOWED_TOOLS
    if unknown:
        return ValidationFailure(
            "SK-VAL-07",
            f"Undeclared/disallowed tool(s): {sorted(unknown)}. Allowed: {sorted(_ALLOWED_TOOLS)}",
        )
    return None


def _val_08_package_size(files: dict[str, str]) -> ValidationFailure | None:
    """SK-VAL-08: Total package size must not exceed MAX_PACKAGE_BYTES."""
    total = sum(len(v.encode("utf-8")) for v in files.values())
    if total > MAX_PACKAGE_BYTES:
        return ValidationFailure(
            "SK-VAL-08",
            f"Package size {total:,} bytes exceeds max {MAX_PACKAGE_BYTES:,} bytes",
        )
    return None


def _val_09_no_binary_files(files: dict[str, str]) -> ValidationFailure | None:
    """SK-VAL-09: No binary file extensions."""
    for path in files:
        ext = "." + path.rsplit(".", 1)[-1].lower() if "." in path else ""
        if ext in _BINARY_EXTS:
            return ValidationFailure("SK-VAL-09", f"Binary file not allowed: {path!r}", path)
    return None


def _val_10_no_secrets(files: dict[str, str]) -> ValidationFailure | None:
    """SK-VAL-10: No secret/credential patterns in any file."""
    for path, content in files.items():
        for pattern in _SECRET_PATTERNS:
            if pattern.search(content):
                return ValidationFailure(
                    "SK-VAL-10",
                    f"Potential secret/credential pattern found in {path!r}",
                    path,
                )
    return None


# ---------------------------------------------------------------------------
# Full validator
# ---------------------------------------------------------------------------

_ALL_RULES = [
    _val_01_skill_md_exists,
    _val_02_valid_name,
    _val_03_valid_version,
    _val_04_has_description,
    _val_05_no_path_traversal,
    _val_06_no_absolute_paths,
    _val_07_allowed_tools,
    _val_08_package_size,
    _val_09_no_binary_files,
    _val_10_no_secrets,
]


@dataclass
class SkillValidationResult:
    valid: bool
    failures: list[ValidationFailure]

    def first_failure(self) -> ValidationFailure | None:
        return self.failures[0] if self.failures else None


def validate_skill_package(files: dict[str, str]) -> SkillValidationResult:
    """
    Run all 10 validation rules against the given file set.
    Returns SkillValidationResult with all failures (not just the first).
    files: {relative_path: content_string}
    """
    failures: list[ValidationFailure] = []
    for rule_fn in _ALL_RULES:
        result = rule_fn(files)
        if result is not None:
            failures.append(result)
    return SkillValidationResult(valid=len(failures) == 0, failures=failures)
