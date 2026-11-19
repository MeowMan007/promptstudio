"""
TSK-070: Prompt assets, versions, blocks, variables.

A PromptAsset is an immutable versioned unit that the model adapter uses.
Key invariants:
  - Once published, a version is immutable (content sealed).
  - Variables are references only — secret values are never stored inline.
  - A PromptAsset is composed of ordered PromptBlocks.
  - Each new edit creates a new PromptVersion (append-only).

Provides:
  - PromptVariable, PromptBlock, PromptVersion, PromptAsset
  - render_prompt(version, variable_values): → rendered string
  - new_version(asset, blocks, variables): → PromptVersion (sealed)
"""
from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Variable types
# ---------------------------------------------------------------------------

class VariableKind(str, Enum):
    STRING   = "string"
    SECRET   = "secret"    # Reference only — never stored inline
    ARTIFACT = "artifact"  # Resolved at run time from project graph
    SYSTEM   = "system"    # Injected by runtime (e.g. current_date)


@dataclass
class PromptVariable:
    """
    A named slot in a prompt template.
    Secret variables hold only a reference (vault key), never the value.
    """
    name: str                        # e.g. "artifact_body" or "api_key"
    kind: VariableKind
    description: str = ""
    default_value: str | None = None # None for SECRET (never stored)
    secret_ref: str | None = None    # vault key, e.g. "vault:openai/api_key"
    required: bool = True

    def __post_init__(self) -> None:
        if self.kind == VariableKind.SECRET and self.default_value is not None:
            raise ValueError(
                f"Variable {self.name!r}: secret variables cannot have a default_value. "
                "Use secret_ref to point to a vault key."
            )


# ---------------------------------------------------------------------------
# Blocks
# ---------------------------------------------------------------------------

class BlockKind(str, Enum):
    SYSTEM    = "system"      # System instructions
    USER      = "user"        # User turn content
    ASSISTANT = "assistant"   # Primed assistant output
    TEMPLATE  = "template"    # Jinja2-lite template with {{variable}} slots


@dataclass
class PromptBlock:
    """An ordered unit of a prompt. Blocks are assembled in order."""
    kind: BlockKind
    content: str              # May contain {{variable_name}} placeholders
    label: str = ""           # Optional human label for the block


# ---------------------------------------------------------------------------
# Versions (immutable once sealed)
# ---------------------------------------------------------------------------

@dataclass
class PromptVersion:
    """
    An immutable version of a prompt asset.
    Once sealed=True, blocks and variables cannot be modified.
    """
    version_id: str
    asset_id: str
    version_number: int
    blocks: list[PromptBlock]
    variables: list[PromptVariable]
    sealed: bool = False
    content_hash: str = ""
    created_at: float = field(default_factory=time.monotonic)
    created_by: str = "system"

    def seal(self) -> None:
        """Seal this version (compute hash, mark immutable)."""
        if self.sealed:
            return
        self.content_hash = _hash_version(self)
        self.sealed = True

    def __setattr__(self, name: str, value: Any) -> None:
        if getattr(self, "sealed", False) and name not in ("sealed",):
            raise AttributeError(
                f"PromptVersion {self.version_id!r} is sealed and immutable"
            )
        super().__setattr__(name, value)


def _hash_version(version: PromptVersion) -> str:
    """Deterministic SHA-256 of a prompt version's content."""
    import json
    canonical = json.dumps({
        "version_id": version.version_id,
        "blocks": [{"kind": b.kind, "content": b.content} for b in version.blocks],
        "variables": [{"name": v.name, "kind": v.kind} for v in version.variables],
    }, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return f"sha256:{hashlib.sha256(canonical.encode()).hexdigest()}"


# ---------------------------------------------------------------------------
# Asset (container of versions)
# ---------------------------------------------------------------------------

@dataclass
class PromptAsset:
    """
    A named, versioned prompt asset.
    Versions are append-only; the latest is `versions[-1]`.
    """
    id: str
    name: str
    description: str = ""
    versions: list[PromptVersion] = field(default_factory=list)
    created_by: str = "system"
    created_at: float = field(default_factory=time.monotonic)
    tags: list[str] = field(default_factory=list)

    def latest_version(self) -> PromptVersion | None:
        return self.versions[-1] if self.versions else None

    def get_version(self, version_number: int) -> PromptVersion | None:
        return next((v for v in self.versions if v.version_number == version_number), None)

    def add_version(self, version: PromptVersion) -> None:
        if not version.sealed:
            raise ValueError("Only sealed versions can be added to a PromptAsset")
        self.versions.append(version)


# ---------------------------------------------------------------------------
# Version factory
# ---------------------------------------------------------------------------

_VAR_RE = re.compile(r"\{\{(\w+)\}\}")


def new_version(
    asset: PromptAsset,
    blocks: list[PromptBlock],
    variables: list[PromptVariable],
    *,
    created_by: str = "system",
) -> PromptVersion:
    """
    Create a new sealed PromptVersion and add it to the asset.
    Validates that all {{variable}} references in blocks have matching variables.
    """
    var_names = {v.name for v in variables}
    for block in blocks:
        for ref in _VAR_RE.findall(block.content):
            if ref not in var_names:
                raise ValueError(
                    f"Block references undefined variable {ref!r}. "
                    f"Declared variables: {sorted(var_names)}"
                )

    version_number = len(asset.versions) + 1
    version_id = f"{asset.id}:v{version_number}"

    version = PromptVersion(
        version_id=version_id,
        asset_id=asset.id,
        version_number=version_number,
        blocks=blocks,
        variables=variables,
        created_by=created_by,
    )
    version.seal()
    asset.add_version(version)
    return version


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------

def render_prompt(
    version: PromptVersion,
    variable_values: dict[str, str],
    *,
    allow_missing: bool = False,
) -> str:
    """
    Render a PromptVersion into a final prompt string.
    Substitutes {{variable_name}} placeholders with values.
    Secret variables must be resolved to their values before calling this.

    Parameters
    ----------
    version: The sealed PromptVersion to render.
    variable_values: Resolved {name: value} map (secrets pre-resolved by caller).
    allow_missing: If False, raises KeyError on missing required variables.
    """
    var_map: dict[str, str] = {}
    for var in version.variables:
        if var.kind == VariableKind.SECRET:
            # Secret values must be injected by the caller (never default)
            if var.name not in variable_values and var.required:
                if not allow_missing:
                    raise KeyError(
                        f"Secret variable {var.name!r} must be resolved before rendering"
                    )
        val = variable_values.get(var.name)
        if val is None and var.default_value is not None:
            val = var.default_value
        if val is None and var.required and not allow_missing:
            raise KeyError(f"Required variable {var.name!r} not provided")
        var_map[var.name] = val or ""

    parts: list[str] = []
    for block in version.blocks:
        content = _VAR_RE.sub(lambda m: var_map.get(m.group(1), f"[{m.group(1)}]"), block.content)
        parts.append(content.strip())
    return "\n\n".join(p for p in parts if p)
