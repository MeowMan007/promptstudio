from __future__ import annotations

import secrets
import time

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_ALIAS_PREFIXES = {
    "brief": "BRF",
    "idea": "IDE",
    "note": "NOT",
    "question": "QST",
    "assumption": "ASM",
    "hypothesis": "HYP",
    "alternative": "ALT",
    "insight": "INS",
    "problem": "PRB",
    "persona": "PER",
    "user_story": "USR",
    "requirement": "REQ",
    "constraint": "CNS",
    "feature": "FEA",
    "exclusion": "EXC",
    "decision": "DEC",
    "adr": "ADR",
    "risk": "RSK",
    "issue": "ISS",
    "user_flow": "FLW",
    "screen": "SCR",
    "wireframe_component": "WFC",
    "interaction": "INT",
    "ui_state": "UIS",
    "design_token": "DTK",
    "component_spec": "CSP",
    "accessibility_rule": "ACR",
    "component": "CMP",
    "data_entity": "ENT",
    "api_endpoint": "API",
    "event_contract": "EVT",
    "integration": "IGT",
    "environment": "ENV",
    "prompt": "PRM",
    "prompt_block": "PBL",
    "prompt_variable": "PVA",
    "prompt_flow": "PFL",
    "field_binding": "FBD",
    "tool_definition": "TDF",
    "skill": "SKL",
    "test_case": "TST",
    "evaluation_case": "EVC",
    "threat": "THR",
    "metric": "MET",
    "epic": "EPC",
    "task": "TSK",
    "milestone": "MLS",
    "source": "SRC",
    "attachment": "ATT",
    "claim": "CLM",
}


def new_ulid() -> str:
    value = (time.time_ns() // 1_000_000 << 80) | secrets.randbits(80)
    encoded = ["0"] * 26
    for index in range(25, -1, -1):
        encoded[index] = _CROCKFORD[value & 31]
        value >>= 5
    return "".join(encoded)


def new_prefixed_id(prefix: str) -> str:
    if len(prefix) != 3 or not prefix.isascii() or not prefix.isalpha() or not prefix.islower():
        raise ValueError("ID prefix must be three lowercase ASCII letters")
    return f"{prefix}_{new_ulid()}"


def new_project_id() -> str:
    return new_prefixed_id("prj")


def new_artifact_id() -> str:
    return new_prefixed_id("art")


def new_edge_id() -> str:
    return new_prefixed_id("edg")


def new_revision_id() -> str:
    return new_prefixed_id("rev")


def new_run_id() -> str:
    return new_prefixed_id("run")


def new_patch_id() -> str:
    return new_prefixed_id("pat")


def new_export_id() -> str:
    return new_prefixed_id("exp")


def alias_prefix_for_type(artifact_type: str) -> str:
    try:
        return _ALIAS_PREFIXES[artifact_type]
    except KeyError as exc:
        raise ValueError(f"No alias prefix registered for artifact type: {artifact_type}") from exc


async def allocate_artifact_identity(
    session: AsyncSession,
    *,
    project_id: str,
    artifact_type: str,
) -> tuple[str, str]:
    """Allocate an artifact ID and alias inside the caller's creation transaction."""
    prefix = alias_prefix_for_type(artifact_type)
    result = await session.execute(
        text(
            """
            INSERT INTO project_alias_counters (project_id, prefix, next_value)
            SELECT p.id, :prefix, 2
            FROM projects AS p
            WHERE p.id = :project_id AND p.status = 'active'
            ON CONFLICT (project_id, prefix) DO UPDATE
              SET next_value = project_alias_counters.next_value + 1
              WHERE project_alias_counters.next_value < 1000000
            RETURNING next_value - 1
            """
        ),
        {"project_id": project_id, "prefix": prefix},
    )
    number = result.scalar_one_or_none()
    if number is None:
        raise ValueError("Project is unavailable or the alias counter is exhausted")
    return new_artifact_id(), f"{prefix}-{number:03d}"
