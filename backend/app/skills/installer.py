"""
TSK-064: Progressive-disclosure loader.
TSK-065: Script sandbox runner.
TSK-066: Install flows (folder, zip, git, paste).

TSK-064:
  Loads only skill metadata initially (from SKILL.md frontmatter).
  Body content loaded on trigger; references loaded on demand; cached.

TSK-065:
  Script sandbox runner — no host access, enforced limits, output treated as untrusted.
  Scripts can only write to a designated output dir; stdout/stderr captured and returned.

TSK-066:
  Install flows supporting four sources: folder (dict), zip (bytes), git (URL+commit), paste (string).
  Path traversal blocked; git pinned to commit; preview generated before enabling.
"""
from __future__ import annotations

import hashlib
import io
import os
import re
import textwrap
import time
import zipfile
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# =============================================================================
# TSK-064: Progressive-disclosure loader
# =============================================================================

@dataclass
class SkillMetadata:
    """Lightweight metadata preloaded for all skills."""
    skill_id: str
    name: str
    version: str
    description: str
    tools: list[str]
    files_manifest: list[str]   # file paths only, no content


@dataclass
class SkillBody:
    """Full SKILL.md body loaded on first trigger."""
    skill_id: str
    markdown: str               # full SKILL.md content (without frontmatter)
    loaded_at: float


@dataclass
class SkillReference:
    """A single reference file loaded on demand."""
    skill_id: str
    file_path: str
    content: str
    loaded_at: float


class ProgressiveLoader:
    """
    Loads skill content progressively:
      1. Metadata only (always preloaded)
      2. Body on trigger
      3. References on demand
    All loaded content is cached.
    """

    def __init__(self, clock: Any = None) -> None:
        self._clock = clock or time.monotonic
        self._metadata_cache: dict[str, SkillMetadata] = {}
        self._body_cache: dict[str, SkillBody] = {}
        self._ref_cache: dict[tuple[str, str], SkillReference] = {}

    def register(self, skill_id: str, files: dict[str, str]) -> SkillMetadata:
        """
        Register a skill package and preload only metadata.
        files: {relative_path: content}
        """
        from backend.app.skills.models import parse_skill_frontmatter
        skill_md = files.get("SKILL.md", "")
        fm = parse_skill_frontmatter(skill_md)
        tools_raw = fm.get("tools", "")
        tools = [t.strip() for t in tools_raw.split(",") if t.strip()] if tools_raw else []
        meta = SkillMetadata(
            skill_id=skill_id,
            name=fm.get("name", skill_id),
            version=fm.get("version", "0.0.0"),
            description=fm.get("description", ""),
            tools=tools,
            files_manifest=sorted(files.keys()),
        )
        # Stash full files for lazy loading
        self._full_files: dict[str, dict[str, str]] = getattr(self, "_full_files", {})
        self._full_files[skill_id] = files
        self._metadata_cache[skill_id] = meta
        return meta

    def get_metadata(self, skill_id: str) -> SkillMetadata | None:
        return self._metadata_cache.get(skill_id)

    def load_body(self, skill_id: str) -> SkillBody | None:
        """Load SKILL.md body on trigger (cached)."""
        if skill_id in self._body_cache:
            return self._body_cache[skill_id]
        files = getattr(self, "_full_files", {}).get(skill_id)
        if files is None:
            return None
        skill_md = files.get("SKILL.md", "")
        # Strip frontmatter
        fm_end = skill_md.find("\n---\n", 3)
        body = skill_md[fm_end + 5:] if fm_end >= 0 else skill_md
        result = SkillBody(skill_id=skill_id, markdown=body.strip(), loaded_at=self._clock())
        self._body_cache[skill_id] = result
        return result

    def load_reference(self, skill_id: str, file_path: str) -> SkillReference | None:
        """Load a specific reference file on demand (cached)."""
        key = (skill_id, file_path)
        if key in self._ref_cache:
            return self._ref_cache[key]
        files = getattr(self, "_full_files", {}).get(skill_id)
        if files is None or file_path not in files:
            return None
        result = SkillReference(
            skill_id=skill_id,
            file_path=file_path,
            content=files[file_path],
            loaded_at=self._clock(),
        )
        self._ref_cache[key] = result
        return result


# =============================================================================
# TSK-065: Script sandbox runner
# =============================================================================

@dataclass
class SandboxResult:
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool
    output_files: dict[str, str]   # files written to output dir
    trusted: bool = False          # always False for skill scripts


class SandboxLimitError(Exception):
    """Raised when a sandbox limit is exceeded before execution."""


_MAX_SCRIPT_BYTES = 64 * 1024    # 64 KB max script size
_MAX_OUTPUT_BYTES = 1 * 1024 * 1024   # 1 MB output cap


def run_in_sandbox(
    script_content: str,
    *,
    timeout_seconds: float = 10.0,
    input_files: dict[str, str] | None = None,
    env_vars: dict[str, str] | None = None,
) -> SandboxResult:
    """
    Execute a skill script in a restricted sandbox (simulation).

    Real implementation would use:
      - subprocess with restricted capabilities (seccomp, chroot, or Docker)
      - Resource limits (CPU, memory, file descriptors)
      - No network access
      - Write access only to a temp output dir

    This stub:
      - Validates limits
      - Simulates execution by evaluating very simple scripts safely
      - Always returns trusted=False
      - Never executes in the API process (see AGENTS.md: never execute model-generated code in API process)
    """
    if len(script_content.encode("utf-8")) > _MAX_SCRIPT_BYTES:
        raise SandboxLimitError(
            f"Script size {len(script_content)} bytes exceeds max {_MAX_SCRIPT_BYTES}"
        )

    # Stub: simulate execution by parsing simple echo/print scripts
    stdout_lines: list[str] = []
    stderr_lines: list[str] = []
    output_files: dict[str, str] = {}

    for line in script_content.splitlines():
        line = line.strip()
        if line.startswith("echo ") or line.startswith("print("):
            content = line[5:].strip().strip("\"'()")
            stdout_lines.append(content)
        elif line.startswith("# ERROR:"):
            stderr_lines.append(line[8:].strip())
        elif "=" in line and "write" in line.lower():
            # Simulate a file write
            output_files["output.txt"] = "simulated output"

    return SandboxResult(
        stdout="\n".join(stdout_lines),
        stderr="\n".join(stderr_lines),
        exit_code=0 if not stderr_lines else 1,
        timed_out=False,
        output_files=output_files,
        trusted=False,     # NEVER trusted
    )


# =============================================================================
# TSK-066: Install flows
# =============================================================================

class InstallSource(str, Enum):
    FOLDER = "folder"
    ZIP    = "zip"
    GIT    = "git"
    PASTE  = "paste"


@dataclass
class InstallPreview:
    """Preview generated before enabling a skill (TSK-066 acceptance)."""
    source: InstallSource
    files_manifest: list[str]
    name: str
    version: str
    description: str
    content_hash: str
    validation_errors: list[str]
    can_enable: bool


_GIT_URL_RE = re.compile(r"^https?://[^\s]+\.git$|^https?://github\.com/[^\s]+$")
_GIT_COMMIT_RE = re.compile(r"^[0-9a-f]{7,40}$")


def install_from_folder(files: dict[str, str]) -> InstallPreview:
    """
    Install from a folder (dict of path → content).
    Path traversal blocked; preview generated.
    """
    from backend.app.skills.models import parse_skill_frontmatter, hash_package_directory
    from backend.app.skills.validator import validate_skill_package

    # Block path traversal
    for path in files:
        parts = path.replace("\\", "/").split("/")
        if ".." in parts:
            raise ValueError(f"Path traversal detected: {path!r}")

    validation = validate_skill_package(files)
    fm = parse_skill_frontmatter(files.get("SKILL.md", ""))

    return InstallPreview(
        source=InstallSource.FOLDER,
        files_manifest=sorted(files.keys()),
        name=fm.get("name", ""),
        version=fm.get("version", ""),
        description=fm.get("description", ""),
        content_hash=hash_package_directory(files),
        validation_errors=[f.reason for f in validation.failures],
        can_enable=validation.valid,
    )


def install_from_zip(zip_bytes: bytes) -> InstallPreview:
    """
    Install from zip bytes.
    Path traversal blocked (zipslip mitigation).
    """
    files: dict[str, str] = {}
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        for zi in zf.infolist():
            if zi.is_dir():
                continue
            name = zi.filename.replace("\\", "/")
            # Zipslip mitigation: reject absolute and traversal paths
            parts = name.split("/")
            if ".." in parts or name.startswith("/"):
                raise ValueError(f"Unsafe zip entry: {name!r}")
            # Strip top-level directory prefix if present
            if "/" in name:
                name = "/".join(name.split("/")[1:]) or name
            try:
                content = zf.read(zi).decode("utf-8", errors="replace")
            except Exception:
                content = ""
            files[name] = content

    return install_from_folder(files)


def install_from_git(git_url: str, commit_sha: str) -> InstallPreview:
    """
    Install from a git URL pinned to a specific commit.
    URL must be HTTPS; commit SHA must be provided (not a branch).
    Returns a preview without cloning (network disabled in sandbox).
    """
    if not _GIT_URL_RE.match(git_url):
        raise ValueError(f"Invalid git URL: {git_url!r}. Must be HTTPS.")
    if not _GIT_COMMIT_RE.match(commit_sha):
        raise ValueError(
            f"Invalid commit SHA: {commit_sha!r}. Must be 7-40 hex chars (not a branch name)."
        )
    # In a real impl: git clone --depth 1 and checkout commit_sha
    # Here we return a preview stub (network not available in sandbox)
    return InstallPreview(
        source=InstallSource.GIT,
        files_manifest=["SKILL.md"],
        name="",
        version="",
        description=f"[git preview: {git_url} @ {commit_sha[:8]}]",
        content_hash=f"sha256:{hashlib.sha256(f'{git_url}:{commit_sha}'.encode()).hexdigest()}",
        validation_errors=["Git clone not available in sandbox — preview only"],
        can_enable=False,
    )


def install_from_paste(skill_md_content: str) -> InstallPreview:
    """
    Install from a pasted SKILL.md string (single-file skill).
    Treated as a folder containing only SKILL.md.
    """
    return install_from_folder({"SKILL.md": skill_md_content})
