"""TSK-099: Screen/token/skill/prompt exporters + llms.txt.

Implements spec sections 23 and 25.5:
  - generate_llms_txt(): llms.txt per spec (project-level AI context file)
  - export_design_tokens(): DTCG-format JSON token export
  - export_skill_package(): verbatim skill package export
  - export_prompt_asset(): prompt asset export with version history
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# llms.txt generator (spec 23 — llms.txt spec)
# ---------------------------------------------------------------------------

@dataclass
class LLMSContext:
    """Context for llms.txt generation."""
    project_name: str
    description: str
    # Short summary for LLMs (the "overview" section)
    overview: str = ""
    # Docs / pages / files to link
    docs_links: list[str] = field(default_factory=list)
    api_links: list[str] = field(default_factory=list)
    # Sections to block from LLM context
    blocked_sections: list[str] = field(default_factory=list)
    # Optional: custom directives
    directives: dict[str, str] = field(default_factory=dict)


def generate_llms_txt(ctx: LLMSContext) -> str:
    """Generate a llms.txt file per the llmstxt.org specification.

    Format:
      # <Project>
      > <description>

      ## Overview
      <overview>

      ## Docs
      - <url>

      ## API
      - <url>

      ## Blocked
      <section> (if any)
    """
    parts: list[str] = [
        f"# {ctx.project_name}",
        f"> {ctx.description}",
        "",
    ]

    if ctx.overview:
        parts += ["## Overview", "", ctx.overview, ""]

    if ctx.docs_links:
        parts.append("## Docs")
        parts.append("")
        for link in ctx.docs_links:
            parts.append(f"- {link}")
        parts.append("")

    if ctx.api_links:
        parts.append("## API")
        parts.append("")
        for link in ctx.api_links:
            parts.append(f"- {link}")
        parts.append("")

    if ctx.blocked_sections:
        parts.append("## Blocked")
        parts.append("")
        for section in ctx.blocked_sections:
            parts.append(f"- {section}")
        parts.append("")

    if ctx.directives:
        parts.append("## Directives")
        parts.append("")
        for key, value in sorted(ctx.directives.items()):
            parts.append(f"{key}: {value}")
        parts.append("")

    body = "\n".join(parts)
    return body


# ---------------------------------------------------------------------------
# Design token exporter (DTCG format — Design Token Community Group)
# ---------------------------------------------------------------------------

@dataclass
class DesignToken:
    name: str
    value: Any
    token_type: str   # "color" | "dimension" | "font-weight" | "duration" | etc.
    description: str = ""
    group: str = ""   # e.g. "color/brand", "spacing"


def _build_dtcg_tree(tokens: list[DesignToken]) -> dict[str, Any]:
    """Build a nested DTCG dict from a flat token list."""
    root: dict[str, Any] = {}
    for token in sorted(tokens, key=lambda t: (t.group, t.name)):
        node = root
        if token.group:
            for part in token.group.split("/"):
                node = node.setdefault(part, {})
        entry: dict[str, Any] = {
            "$value": token.value,
            "$type": token.token_type,
        }
        if token.description:
            entry["$description"] = token.description
        node[token.name] = entry
    return root


def export_design_tokens(tokens: list[DesignToken]) -> str:
    """Export design tokens as DTCG-format JSON string (deterministic)."""
    tree = _build_dtcg_tree(tokens)
    return json.dumps(tree, sort_keys=True, indent=2) + "\n"


# ---------------------------------------------------------------------------
# Skill package exporter
# ---------------------------------------------------------------------------

@dataclass
class SkillPackageExport:
    """A skill package ready for export."""
    package_id: str
    name: str
    version: str
    files: dict[str, bytes]   # relative_path → file bytes (verbatim)
    metadata: dict[str, Any] = field(default_factory=dict)


def export_skill_package(pkg: SkillPackageExport) -> dict[str, Any]:
    """Export a skill package as a manifest dict.

    Files are exported verbatim (bytes → base64-free dict for now;
    the archive step in pipeline.py will zip them).

    Returns a manifest dict containing file checksums and metadata.
    """
    file_checksums: dict[str, str] = {}
    for path, content in sorted(pkg.files.items()):
        digest = hashlib.sha256(content).hexdigest()
        file_checksums[path] = digest

    manifest_checksum = hashlib.sha256(
        json.dumps(file_checksums, sort_keys=True).encode()
    ).hexdigest()[:16]

    return {
        "package_id": pkg.package_id,
        "name": pkg.name,
        "version": pkg.version,
        "files": file_checksums,
        "metadata": pkg.metadata,
        "manifest_checksum": manifest_checksum,
    }


# ---------------------------------------------------------------------------
# Prompt asset exporter
# ---------------------------------------------------------------------------

@dataclass
class PromptVersionExport:
    version: int
    content: str
    variables: list[str]
    created_at: str   # ISO-8601


@dataclass
class PromptAssetExport:
    asset_id: str
    name: str
    current_version: int
    versions: list[PromptVersionExport]
    tags: list[str] = field(default_factory=list)


def export_prompt_asset(asset: PromptAssetExport) -> dict[str, Any]:
    """Export a prompt asset with full version history."""
    versions_data = [
        {
            "version": v.version,
            "content": v.content,
            "variables": sorted(v.variables),
            "created_at": v.created_at,
            "content_hash": hashlib.sha256(v.content.encode()).hexdigest()[:16],
        }
        for v in sorted(asset.versions, key=lambda v: v.version)
    ]

    payload: dict[str, Any] = {
        "asset_id": asset.asset_id,
        "name": asset.name,
        "current_version": asset.current_version,
        "tags": sorted(asset.tags),
        "versions": versions_data,
    }

    checksum = hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()[:16]
    payload["export_checksum"] = checksum

    return payload
