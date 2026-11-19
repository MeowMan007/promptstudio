"""
TSK-062: Trust levels + enable/disable + audit.
TSK-063: Permission intersection (skill × run × role × policy).

Trust levels:
  untrusted  — newly imported skills, not enabled by default
  community  — vetted by the community, can be enabled by owners
  official   — first-party skills, always available

A skill can NEVER widen permissions beyond what the caller role allows.
Effective permission set = skill_permissions ∩ caller_permissions.

Provides:
  - TrustLevel: enum
  - SkillPermission: individual permission flag
  - SkillTrustPolicy: maps trust level → allowed permissions
  - effective_permissions(skill_trust, skill_declared, caller_role): → frozenset
  - enable_skill / disable_skill (audit-generating operations)
  - AuditEvent: simple audit record
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Trust levels
# ---------------------------------------------------------------------------

class TrustLevel(str, Enum):
    UNTRUSTED  = "untrusted"
    COMMUNITY  = "community"
    OFFICIAL   = "official"


# ---------------------------------------------------------------------------
# Permission flags
# ---------------------------------------------------------------------------

class SkillPermission(str, Enum):
    READ_ARTIFACTS   = "read_artifacts"
    PROPOSE_PATCH    = "propose_patch"
    APPLY_PATCH      = "apply_patch"           # ALWAYS requires human approval
    RUN_FIELD        = "run_field"
    ASSEMBLE_CONTEXT = "assemble_context"
    READ_WEB         = "read_web"
    RUN_COMMAND      = "run_command"            # sandboxed only
    WRITE_FILE       = "write_file"             # skill output dir only


# Permissions available at each trust level (ceiling)
_TRUST_CEILING: dict[TrustLevel, frozenset[SkillPermission]] = {
    TrustLevel.UNTRUSTED: frozenset({
        SkillPermission.READ_ARTIFACTS,
        SkillPermission.ASSEMBLE_CONTEXT,
    }),
    TrustLevel.COMMUNITY: frozenset({
        SkillPermission.READ_ARTIFACTS,
        SkillPermission.ASSEMBLE_CONTEXT,
        SkillPermission.PROPOSE_PATCH,
        SkillPermission.RUN_FIELD,
        SkillPermission.READ_WEB,
    }),
    TrustLevel.OFFICIAL: frozenset(SkillPermission),   # all permissions
}

# Permissions available at each caller role (ceiling)
_ROLE_CEILING: dict[str, frozenset[SkillPermission]] = {
    "viewer":       frozenset({SkillPermission.READ_ARTIFACTS}),
    "editor":       frozenset({
        SkillPermission.READ_ARTIFACTS,
        SkillPermission.ASSEMBLE_CONTEXT,
        SkillPermission.PROPOSE_PATCH,
        SkillPermission.RUN_FIELD,
        SkillPermission.READ_WEB,
    }),
    "owner":        frozenset(SkillPermission),
    "admin":        frozenset(SkillPermission),
    "trusted_skill": frozenset(SkillPermission),
}


def effective_permissions(
    trust_level: TrustLevel,
    skill_declared: set[SkillPermission] | frozenset[SkillPermission],
    caller_role: str,
) -> frozenset[SkillPermission]:
    """
    Compute the effective permission set for a skill invocation.
    effective = skill_declared ∩ trust_ceiling(trust) ∩ role_ceiling(role)

    A skill can NEVER widen permissions beyond what the caller role allows.
    """
    trust_ceiling = _TRUST_CEILING.get(trust_level, frozenset())
    role_ceiling = _ROLE_CEILING.get(caller_role, frozenset())
    return frozenset(skill_declared) & trust_ceiling & role_ceiling


# ---------------------------------------------------------------------------
# Audit events
# ---------------------------------------------------------------------------

@dataclass
class AuditEvent:
    event_type: str         # "skill_enabled" | "skill_disabled" | "trust_changed"
    skill_id: str
    actor: str              # who triggered the event
    timestamp: float
    detail: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Enable / disable (audit-generating)
# ---------------------------------------------------------------------------

@dataclass
class SkillRegistry:
    """
    In-memory registry tracking enabled skills and audit log.
    Real impl backed by DB.
    """
    _enabled: dict[str, bool] = field(default_factory=dict)      # skill_id → enabled
    _trust: dict[str, TrustLevel] = field(default_factory=dict)  # skill_id → trust
    _audit: list[AuditEvent] = field(default_factory=list)
    _clock: Any = None

    def _now(self) -> float:
        return self._clock() if self._clock else time.monotonic()

    def register(
        self,
        skill_id: str,
        trust_level: TrustLevel = TrustLevel.UNTRUSTED,
    ) -> None:
        """Register a skill. Imported skills start disabled."""
        self._trust[skill_id] = trust_level
        # Official skills start enabled; all others start disabled (TSK-062 acceptance)
        self._enabled[skill_id] = trust_level == TrustLevel.OFFICIAL

    def enable(self, skill_id: str, actor: str) -> AuditEvent:
        """Enable a skill. Generating an audit event."""
        if skill_id not in self._trust:
            raise KeyError(f"Skill {skill_id!r} not registered")
        self._enabled[skill_id] = True
        event = AuditEvent(
            event_type="skill_enabled",
            skill_id=skill_id,
            actor=actor,
            timestamp=self._now(),
            detail={"trust_level": self._trust[skill_id]},
        )
        self._audit.append(event)
        return event

    def disable(self, skill_id: str, actor: str) -> AuditEvent:
        """Disable a skill. Generating an audit event."""
        if skill_id not in self._trust:
            raise KeyError(f"Skill {skill_id!r} not registered")
        self._enabled[skill_id] = False
        event = AuditEvent(
            event_type="skill_disabled",
            skill_id=skill_id,
            actor=actor,
            timestamp=self._now(),
            detail={"trust_level": self._trust[skill_id]},
        )
        self._audit.append(event)
        return event

    def set_trust(self, skill_id: str, trust_level: TrustLevel, actor: str) -> AuditEvent:
        """Change trust level. Generates audit event."""
        if skill_id not in self._trust:
            raise KeyError(f"Skill {skill_id!r} not registered")
        old = self._trust[skill_id]
        self._trust[skill_id] = trust_level
        event = AuditEvent(
            event_type="trust_changed",
            skill_id=skill_id,
            actor=actor,
            timestamp=self._now(),
            detail={"from": old, "to": trust_level},
        )
        self._audit.append(event)
        return event

    def is_enabled(self, skill_id: str) -> bool:
        return self._enabled.get(skill_id, False)

    def trust_level(self, skill_id: str) -> TrustLevel:
        return self._trust.get(skill_id, TrustLevel.UNTRUSTED)

    def audit_log(self) -> list[AuditEvent]:
        return list(self._audit)
