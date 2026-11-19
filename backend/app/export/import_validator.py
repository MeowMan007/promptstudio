"""TSK-100: Import validator + clean-import round-trip gate.

Implements spec section 26.4:
  - ImportPackage: validated import structure
  - validate_import(): structural validation + collision detection
  - id_map: collision resolution on import
  - round_trip_check(): export → import → export → checksum comparison
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

class ImportError(ValueError):
    pass


class CollisionStrategy(str, Enum):
    REJECT = "reject"      # Fail if ID already exists
    RENAME = "rename"      # Auto-rename with suffix
    OVERWRITE = "overwrite"


@dataclass
class ImportPackage:
    """Incoming import payload to be validated."""
    package_id: str
    name: str
    version: str
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    skills: list[dict[str, Any]] = field(default_factory=list)
    prompts: list[dict[str, Any]] = field(default_factory=list)
    tokens: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    export_checksum: str = ""


@dataclass
class ImportResult:
    """Result of a validated import."""
    package_id: str
    # id_map: original_id → assigned_id (identity if no collision)
    id_map: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

_REQUIRED_PACKAGE_FIELDS = {"package_id", "name", "version"}


def validate_import(
    package: ImportPackage,
    existing_ids: set[str] | None = None,
    collision_strategy: CollisionStrategy = CollisionStrategy.RENAME,
) -> ImportResult:
    """Validate an import package and resolve ID collisions.

    Args:
        package: The incoming package to validate.
        existing_ids: Set of IDs already in the project (for collision detect).
        collision_strategy: How to handle ID collisions.

    Returns:
        ImportResult with id_map, warnings, and errors.
    """
    existing_ids = existing_ids or set()
    result = ImportResult(package_id=package.package_id)
    errors = result.errors
    warnings = result.warnings

    # --- Structural validation ---
    if not package.package_id:
        errors.append("package_id is required")
    if not package.name:
        errors.append("name is required")
    if not package.version:
        errors.append("version is required")

    # Validate checksum if provided
    if package.export_checksum:
        payload = {
            "package_id": package.package_id,
            "name": package.name,
            "version": package.version,
        }
        recomputed = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode()
        ).hexdigest()[:16]
        # We only warn on mismatch (the checksum is advisory for round-trip gating)
        if recomputed != package.export_checksum:
            warnings.append(
                f"Checksum mismatch: expected {package.export_checksum!r}, "
                f"computed {recomputed!r} — package may have been modified"
            )

    # Validate artifact entries
    for i, artifact in enumerate(package.artifacts):
        if "id" not in artifact:
            errors.append(f"artifacts[{i}] missing 'id'")
        if "type" not in artifact:
            errors.append(f"artifacts[{i}] missing 'type'")

    # Validate skill entries
    for i, skill in enumerate(package.skills):
        if "package_id" not in skill:
            errors.append(f"skills[{i}] missing 'package_id'")

    # Validate prompt entries
    for i, prompt in enumerate(package.prompts):
        if "asset_id" not in prompt:
            errors.append(f"prompts[{i}] missing 'asset_id'")

    if errors:
        return result  # skip collision handling if structurally invalid

    # --- Collision detection & id_map ---
    all_incoming_ids: list[str] = (
        [a["id"] for a in package.artifacts if "id" in a]
        + [s["package_id"] for s in package.skills if "package_id" in s]
        + [p["asset_id"] for p in package.prompts if "asset_id" in p]
    )

    for original_id in all_incoming_ids:
        if original_id in existing_ids:
            if collision_strategy == CollisionStrategy.REJECT:
                errors.append(f"ID collision: {original_id!r} already exists")
                result.id_map[original_id] = original_id
            elif collision_strategy == CollisionStrategy.RENAME:
                suffix = hashlib.sha256(original_id.encode()).hexdigest()[:6]
                new_id = f"{original_id}_{suffix}"
                warnings.append(f"ID collision renamed: {original_id!r} → {new_id!r}")
                result.id_map[original_id] = new_id
            else:  # OVERWRITE
                warnings.append(f"ID collision will overwrite: {original_id!r}")
                result.id_map[original_id] = original_id
        else:
            result.id_map[original_id] = original_id

    return result


# ---------------------------------------------------------------------------
# Round-trip gate (spec 26.4: EX-02 — export → import → export → match)
# ---------------------------------------------------------------------------

class RoundTripError(AssertionError):
    pass


def _stable_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode()
    ).hexdigest()


def round_trip_check(
    original_export: dict[str, Any],
    re_export: dict[str, Any],
    ignore_keys: list[str] | None = None,
) -> None:
    """Assert that two export payloads produce the same stable hash.

    Args:
        original_export: The first export output.
        re_export: The export produced after import of the first.
        ignore_keys: Top-level keys to strip before comparison (e.g. timestamps).

    Raises:
        RoundTripError if the hashes differ.
    """
    ignore_keys = ignore_keys or ["exported_at", "export_checksum"]

    def strip(d: dict[str, Any]) -> dict[str, Any]:
        return {k: v for k, v in d.items() if k not in ignore_keys}

    h1 = _stable_hash(strip(original_export))
    h2 = _stable_hash(strip(re_export))

    if h1 != h2:
        raise RoundTripError(
            f"Round-trip mismatch:\n"
            f"  original hash : {h1}\n"
            f"  re-export hash: {h2}\n"
            "Export and re-export must produce identical content."
        )
