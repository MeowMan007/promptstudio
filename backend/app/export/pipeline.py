"""
TSK-085: Export job model, profiles, revision freezing.
TSK-086: Human doc generators (brief, scope, decisions, risks).
TSK-087: Machine graph + registries + schemas exporter.
TSK-088: Manifest, checksums, deterministic archive writer.
TSK-089: Secret scanner + path safety + redaction.

An ExportJob:
  - Pins the project revision at creation time (immutable snapshot).
  - Selects artifact subsets by ExportProfile.
  - Omissions recorded in the manifest.

Deterministic: two exports of the same revision produce identical checksums.
No model calls in export — purely deterministic transformation.

Acceptance:
  - TSK-085: Job pins revision; profile selects subsets; omissions recorded.
  - TSK-086: Deterministic output; no model calls; TODOs for missing content.
  - TSK-087: Self-describing package; validates standalone.
  - TSK-088: Two exports of same revision produce identical checksums.
  - TSK-089: Hostile fixture blocked; redaction placeholders; report entries.
"""
from __future__ import annotations

import hashlib
import json
import re
import zipfile
import io
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# =============================================================================
# TSK-085: Export job + profiles
# =============================================================================

class ExportProfile(str, Enum):
    FULL        = "full"        # All artifacts
    HUMAN       = "human"       # Human-readable docs only
    MACHINE     = "machine"     # Machine graph + schemas
    BRIEF_ONLY  = "brief_only"  # Just the brief + personas


_PROFILE_TYPES: dict[ExportProfile, set[str] | None] = {
    ExportProfile.FULL: None,     # None = all types
    ExportProfile.HUMAN: {
        "brief", "persona", "user_story", "requirement",
        "decision", "risk", "user_flow", "screen",
    },
    ExportProfile.MACHINE: {
        "data_entity", "api_endpoint", "event_contract",
        "component", "integration", "prompt", "evaluation_case",
    },
    ExportProfile.BRIEF_ONLY: {"brief", "persona"},
}


@dataclass
class ArtifactExportRecord:
    """One artifact in the export."""
    artifact_id: str
    artifact_type: str
    title: str
    body: str
    revision: int
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExportJob:
    """
    Pins a project revision and declares which artifacts to export.
    Omissions (filtered out by profile) are recorded in the manifest.
    """
    job_id: str
    project_id: str
    pinned_revision: int
    profile: ExportProfile
    created_at: float = field(default_factory=time.monotonic)
    created_by: str = "system"


@dataclass
class ExportManifest:
    """
    Describes the contents of one export.
    Omissions are recorded with reasons.
    """
    job_id: str
    project_id: str
    pinned_revision: int
    profile: ExportProfile
    included: list[str]           # artifact_ids included
    omitted: list[dict[str, str]] # [{"artifact_id": ..., "reason": ...}]
    checksum: str                 # sha256 of deterministic serialisation
    created_at: float = field(default_factory=time.monotonic)


def build_manifest(
    job: ExportJob,
    all_artifacts: list[ArtifactExportRecord],
) -> ExportManifest:
    """Build an ExportManifest from a job and full artifact list."""
    allowed_types = _PROFILE_TYPES[job.profile]

    included: list[str] = []
    omitted: list[dict[str, str]] = []

    for art in all_artifacts:
        if allowed_types is None or art.artifact_type in allowed_types:
            included.append(art.artifact_id)
        else:
            omitted.append({
                "artifact_id": art.artifact_id,
                "artifact_type": art.artifact_type,
                "reason": f"Type {art.artifact_type!r} not in profile {job.profile!r}",
            })

    # Deterministic checksum
    canon = json.dumps({
        "job_id": job.job_id,
        "project_id": job.project_id,
        "pinned_revision": job.pinned_revision,
        "profile": job.profile,
        "included": sorted(included),
        "omitted": [o["artifact_id"] for o in sorted(omitted, key=lambda x: x["artifact_id"])],
    }, sort_keys=True, separators=(",", ":")).encode()
    checksum = f"sha256:{hashlib.sha256(canon).hexdigest()}"

    return ExportManifest(
        job_id=job.job_id,
        project_id=job.project_id,
        pinned_revision=job.pinned_revision,
        profile=job.profile,
        included=sorted(included),
        omitted=omitted,
        checksum=checksum,
    )


# =============================================================================
# TSK-086: Human doc generators
# =============================================================================

def generate_brief_doc(artifact: ArtifactExportRecord) -> str:
    """Generate a human-readable brief document. No model calls."""
    body = artifact.body.strip() if artifact.body.strip() else "[TODO: add project brief]"
    return f"# {artifact.title}\n\n{body}\n"


def generate_decision_doc(artifacts: list[ArtifactExportRecord]) -> str:
    """Generate a decision log (ADR-style). No model calls."""
    decisions = [a for a in artifacts if a.artifact_type == "decision"]
    if not decisions:
        return "# Decision Log\n\n[TODO: no decisions recorded yet]\n"
    lines = ["# Decision Log\n"]
    for a in sorted(decisions, key=lambda x: x.artifact_id):
        body = a.body.strip() if a.body.strip() else "[TODO: add decision details]"
        lines.append(f"## {a.title}\n\n{body}\n")
    return "\n".join(lines)


def generate_risk_doc(artifacts: list[ArtifactExportRecord]) -> str:
    """Generate a risk register. No model calls."""
    risks = [a for a in artifacts if a.artifact_type == "risk"]
    if not risks:
        return "# Risk Register\n\n[TODO: no risks recorded yet]\n"
    lines = ["# Risk Register\n"]
    for a in sorted(risks, key=lambda x: x.artifact_id):
        body = a.body.strip() if a.body.strip() else "[TODO: add risk details]"
        lines.append(f"## {a.title}\n\n{body}\n")
    return "\n".join(lines)


def generate_scope_doc(artifacts: list[ArtifactExportRecord]) -> str:
    """Generate a scope doc from brief + user stories. No model calls."""
    briefs = [a for a in artifacts if a.artifact_type == "brief"]
    stories = [a for a in artifacts if a.artifact_type == "user_story"]

    lines = ["# Project Scope\n"]
    if briefs:
        lines.append(f"## Overview\n\n{briefs[0].body.strip()}\n")
    else:
        lines.append("## Overview\n\n[TODO: add project brief]\n")

    if stories:
        lines.append("## User Stories\n")
        for s in sorted(stories, key=lambda x: x.artifact_id):
            lines.append(f"- {s.title}")
    else:
        lines.append("## User Stories\n\n[TODO: add user stories]\n")

    return "\n".join(lines)


# =============================================================================
# TSK-087: Machine graph exporter
# =============================================================================

@dataclass
class MachineExportPackage:
    """Self-describing machine-readable export."""
    project_id: str
    pinned_revision: int
    artifacts: list[dict[str, Any]]   # serialised artifact records
    edge_list: list[dict[str, Any]]   # {source, target, edge_type}
    schemas: dict[str, Any]           # artifact_type → JSON schema
    registry: dict[str, Any]          # tool/binding/skill registrations
    export_version: str = "1.0.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "export_version": self.export_version,
            "project_id": self.project_id,
            "pinned_revision": self.pinned_revision,
            "artifacts": self.artifacts,
            "edge_list": self.edge_list,
            "schemas": self.schemas,
            "registry": self.registry,
        }

    def validates_standalone(self) -> bool:
        """Check the package is self-consistent."""
        artifact_ids = {a["id"] for a in self.artifacts}
        for edge in self.edge_list:
            if edge.get("source") not in artifact_ids:
                return False
            if edge.get("target") not in artifact_ids:
                return False
        return True


def build_machine_package(
    job: ExportJob,
    artifacts: list[ArtifactExportRecord],
    edges: list[dict[str, str]] | None = None,
    schemas: dict[str, Any] | None = None,
    registry: dict[str, Any] | None = None,
) -> MachineExportPackage:
    """Build a MachineExportPackage from an export job."""
    allowed_types = _PROFILE_TYPES.get(job.profile)
    filtered = [
        a for a in artifacts
        if allowed_types is None or a.artifact_type in allowed_types
    ]
    art_dicts = [
        {
            "id": a.artifact_id,
            "type": a.artifact_type,
            "title": a.title,
            "body": a.body,
            "revision": a.revision,
            "payload": a.payload,
        }
        for a in filtered
    ]
    return MachineExportPackage(
        project_id=job.project_id,
        pinned_revision=job.pinned_revision,
        artifacts=sorted(art_dicts, key=lambda x: x["id"]),
        edge_list=edges or [],
        schemas=schemas or {},
        registry=registry or {},
    )


# =============================================================================
# TSK-088: Deterministic archive writer
# =============================================================================

def write_archive(
    job: ExportJob,
    manifest: ExportManifest,
    human_docs: dict[str, str],     # filename → content
    machine_package: MachineExportPackage,
) -> bytes:
    """
    Write a deterministic ZIP archive.
    Two calls with identical inputs produce identical bytes.
    Returns the archive as bytes.
    """
    buf = io.BytesIO()

    # Build all entries sorted by name for determinism
    entries: list[tuple[str, bytes]] = []

    # 1. Manifest
    manifest_json = json.dumps({
        "job_id": manifest.job_id,
        "project_id": manifest.project_id,
        "pinned_revision": manifest.pinned_revision,
        "profile": manifest.profile,
        "included": sorted(manifest.included),
        "omitted": sorted(manifest.omitted, key=lambda x: x["artifact_id"]),
        "checksum": manifest.checksum,
    }, sort_keys=True, indent=2)
    entries.append(("manifest.json", manifest_json.encode()))

    # 2. Machine package
    machine_json = json.dumps(machine_package.to_dict(), sort_keys=True, indent=2)
    entries.append(("machine/graph.json", machine_json.encode()))

    # 3. Human docs (sorted for determinism)
    for fname in sorted(human_docs.keys()):
        entries.append((f"human/{fname}", human_docs[fname].encode()))

    # Write sorted entries with fixed timestamp (epoch) for determinism
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, data in sorted(entries, key=lambda x: x[0]):
            info = zipfile.ZipInfo(filename=name)
            info.date_time = (1980, 1, 1, 0, 0, 0)   # fixed timestamp for determinism
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, data)

    return buf.getvalue()


def checksum_archive(archive_bytes: bytes) -> str:
    """Compute SHA-256 checksum of an archive."""
    return f"sha256:{hashlib.sha256(archive_bytes).hexdigest()}"


# =============================================================================
# TSK-089: Secret scanner + path safety + redaction
# =============================================================================

_SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_\-]?key|secret|password|token)\s*[:=]\s*['\"]?[A-Za-z0-9+/\-_]{16,}"),
    re.compile(r"sk-[A-Za-z0-9\-]{20,}"),          # OpenAI key / project key (allows hyphens)
    re.compile(r"ghp_[A-Za-z0-9]{30,}"),           # GitHub PAT
    re.compile(r"AKIA[A-Z0-9]{12,}"),              # AWS access key ID
    re.compile(r"(?i)aws.{0,20}secret.{0,10}[A-Za-z0-9/+]{20,}"),  # AWS secret
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),  # any PEM private key (RSA/EC/PKCS8)
]

_UNSAFE_PATH_RE = re.compile(r"\.\.[/\\]|^[/\\]|^[A-Za-z]:[/\\]|\x00|[<>|*?]")

REDACTION_PLACEHOLDER = "[REDACTED]"


@dataclass
class ScanReport:
    """Report of one scan."""
    path: str
    findings: list[str]        # human-readable finding descriptions
    redacted: bool = False     # True if content was redacted


def scan_text(text: str, path: str = "<unknown>") -> ScanReport:
    """Scan text content for secret patterns."""
    findings: list[str] = []
    for pattern in _SECRET_PATTERNS:
        if pattern.search(text):
            findings.append(f"Potential secret pattern at {path!r}: {pattern.pattern[:40]}...")
    return ScanReport(path=path, findings=findings)


def redact_text(text: str) -> str:
    """Replace secret patterns with redaction placeholder."""
    result = text
    for pattern in _SECRET_PATTERNS:
        result = pattern.sub(REDACTION_PLACEHOLDER, result)
    return result


def check_path_safety(path: str) -> str | None:
    """
    Check a file path for unsafe patterns (traversal, absolute).
    Returns error string if unsafe, else None.
    """
    if _UNSAFE_PATH_RE.search(path):
        return f"Unsafe path detected: {path!r}"
    return None


def scan_export_package(
    files: dict[str, str],
) -> tuple[dict[str, str], list[ScanReport]]:
    """
    Scan all files in an export package.
    Returns (redacted_files, scan_reports).
    Files with secrets are redacted; all findings reported.
    TSK-089: hostile fixture blocked; redaction placeholders; report entries.
    """
    redacted: dict[str, str] = {}
    reports: list[ScanReport] = []

    for path, content in files.items():
        # Path safety
        path_err = check_path_safety(path)
        if path_err:
            reports.append(ScanReport(path=path, findings=[path_err], redacted=False))
            continue   # Skip unsafe paths entirely

        # Secret scan + redact
        report = scan_text(content, path)
        if report.findings:
            redacted_content = redact_text(content)
            report.redacted = True
            redacted[path] = redacted_content
        else:
            redacted[path] = content

        reports.append(report)

    return redacted, reports
