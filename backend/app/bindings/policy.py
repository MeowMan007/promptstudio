"""
TSK-046: Field locks, cooldowns and per-binding policy enforcement.

Extends the policy model in models.py with server-side enforcement:
  - Locked field: any write attempt → FieldLockError
  - Cooldown: time-based rate limit per (binding, artifact) pair
  - AutoApply: only trusted roles / trusted skills may auto-apply

This module provides:
  - PolicyEnforcer: stateful enforcer (owns cooldown state)
  - enforce_lock(binding): raises FieldLockError if locked
  - check_cooldown(enforcer, binding, artifact_id): raises CooldownError
  - check_auto_apply(binding, caller_role): raises AutoApplyDeniedError
  - record_run(enforcer, binding, artifact_id): update cooldown timestamp
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from backend.app.bindings.models import AutoApplyPolicy, FieldBinding


# ---------------------------------------------------------------------------
# Policy exceptions
# ---------------------------------------------------------------------------

class FieldLockError(Exception):
    """Raised when a write to a locked field is attempted."""
    def __init__(self, field_path: str, binding_id: str) -> None:
        self.field_path = field_path
        self.binding_id = binding_id
        super().__init__(f"Field {field_path!r} is locked by binding {binding_id!r}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": "FIELD_LOCKED",
            "field_path": self.field_path,
            "binding_id": self.binding_id,
        }


class CooldownError(Exception):
    """Raised when a binding is still within its cooldown window."""
    def __init__(self, binding_id: str, remaining_seconds: float) -> None:
        self.binding_id = binding_id
        self.remaining_seconds = remaining_seconds
        super().__init__(
            f"Binding {binding_id!r} is in cooldown for {remaining_seconds:.1f}s more"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": "COOLDOWN_ACTIVE",
            "binding_id": self.binding_id,
            "remaining_seconds": round(self.remaining_seconds, 2),
        }


class AutoApplyDeniedError(Exception):
    """Raised when auto-apply is not permitted for the caller role / policy."""
    def __init__(self, binding_id: str, reason: str) -> None:
        self.binding_id = binding_id
        self.reason = reason
        super().__init__(f"Auto-apply denied for binding {binding_id!r}: {reason}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": "AUTO_APPLY_DENIED",
            "binding_id": self.binding_id,
            "reason": self.reason,
        }


# ---------------------------------------------------------------------------
# Trusted roles / skills
# ---------------------------------------------------------------------------

# Roles that may trigger auto-apply under LOW_RISK policy
_LOW_RISK_ALLOWED_ROLES: frozenset[str] = frozenset({"editor", "owner", "admin", "trusted_skill"})

# Roles that may trigger auto-apply under ALWAYS policy (must be explicitly privileged)
_ALWAYS_ALLOWED_ROLES: frozenset[str] = frozenset({"trusted_skill", "admin"})


# ---------------------------------------------------------------------------
# Policy enforcer
# ---------------------------------------------------------------------------

@dataclass
class PolicyEnforcer:
    """
    Stateful policy enforcer.
    Owns the cooldown clock — inject a custom _clock for testing.
    TSK-103: tenant_id isolates lock/cooldown state between tenants.
    """
    tenant_id: str = "default"
    _last_run_at: dict[str, float] = field(default_factory=dict)
    _clock: Any = field(default=None)   # callable() → float; defaults to time.monotonic
    # Tenant-scoped lock store: (artifact_id, field_path) → locked_by
    _locks: dict[tuple[str, str], str] = field(default_factory=dict)
    # Tenant-scoped simple cooldowns: (artifact_id, field_path) → expires_at
    _cooldowns: dict[tuple[str, str], float] = field(default_factory=dict)

    def _now(self) -> float:
        return self._clock() if self._clock is not None else time.monotonic()

    # -- Tenant-aware convenience lock API (TSK-103) -------------------------

    def lock_field(self, artifact_id: str, field_path: str, locked_by: str) -> None:
        """Lock a field for a specific user (tenant-scoped)."""
        self._locks[(artifact_id, field_path)] = locked_by

    def check_lock(self, artifact_id: str, field_path: str, requesting_user: str) -> None:
        """Raise FieldLockError if another user holds the lock."""
        holder = self._locks.get((artifact_id, field_path))
        if holder is not None and holder != requesting_user:
            # Reuse FieldLockError with synthetic binding_id
            raise FieldLockError(field_path, f"{artifact_id}:{field_path}")

    def set_cooldown(self, artifact_id: str, field_path: str, cooldown_seconds: float) -> None:
        """Set a simple cooldown (tenant-scoped) expiry."""
        self._cooldowns[(artifact_id, field_path)] = self._now() + cooldown_seconds

    def check_cooldown(
        self,
        binding_or_artifact,
        artifact_or_field,
    ) -> None:
        """Polymorphic cooldown check.

        Accepts either:
          check_cooldown(FieldBinding, artifact_id: str)  — original API
          check_cooldown(artifact_id: str, field_path: str)  — convenience API
        """
        if isinstance(binding_or_artifact, str):
            # Convenience API: check simple cooldown store
            key = (binding_or_artifact, artifact_or_field)
            expires_at = self._cooldowns.get(key)
            if expires_at is not None and self._now() < expires_at:
                remaining = expires_at - self._now()
                raise CooldownError(f"{binding_or_artifact}:{artifact_or_field}", remaining)
            return
        # Original FieldBinding API
        binding = binding_or_artifact
        artifact_id = artifact_or_field
        if binding.policy.cooldown_seconds <= 0:
            return
        key_str = self._cooldown_key(binding.id, artifact_id)
        last = self._last_run_at.get(key_str)
        if last is None:
            return
        elapsed = self._now() - last
        remaining = binding.policy.cooldown_seconds - elapsed
        if remaining > 0:
            raise CooldownError(binding.id, remaining)

    def enforce_lock(self, binding: FieldBinding) -> None:
        """Raise FieldLockError if the binding's policy marks the field locked."""
        if binding.policy.locked:
            raise FieldLockError(binding.field_path, binding.id)

    # -- Cooldown check (original FieldBinding API) --------------------------

    def _cooldown_key(self, binding_id: str, artifact_id: str) -> str:
        return f"{binding_id}:{artifact_id}"

    def check_cooldown_binding(self, binding: "FieldBinding", artifact_id: str) -> None:
        """Raise CooldownError if still within cooldown window (FieldBinding API)."""
        if binding.policy.cooldown_seconds <= 0:
            return
        key = self._cooldown_key(binding.id, artifact_id)
        last = self._last_run_at.get(key)
        if last is None:
            return
        elapsed = self._now() - last
        remaining = binding.policy.cooldown_seconds - elapsed
        if remaining > 0:
            raise CooldownError(binding.id, remaining)

    def record_run(self, binding: FieldBinding, artifact_id: str) -> None:
        """Record that a run just completed; starts the cooldown clock."""
        if binding.policy.cooldown_seconds > 0:
            key = self._cooldown_key(binding.id, artifact_id)
            self._last_run_at[key] = self._now()

    # -- Auto-apply check ----------------------------------------------------

    def check_auto_apply(self, binding: FieldBinding, caller_role: str) -> None:
        """
        Raise AutoApplyDeniedError if the caller is not permitted to auto-apply.
        Call this BEFORE applying a proposal without human review.
        """
        policy = binding.policy.auto_apply

        if policy == AutoApplyPolicy.NEVER:
            raise AutoApplyDeniedError(
                binding.id,
                "policy is NEVER — human review required",
            )

        if policy == AutoApplyPolicy.LOW_RISK:
            if caller_role not in _LOW_RISK_ALLOWED_ROLES:
                raise AutoApplyDeniedError(
                    binding.id,
                    f"role {caller_role!r} not in LOW_RISK allowed roles",
                )

        if policy == AutoApplyPolicy.ALWAYS:
            if caller_role not in _ALWAYS_ALLOWED_ROLES:
                raise AutoApplyDeniedError(
                    binding.id,
                    f"role {caller_role!r} not in ALWAYS allowed roles — only trusted_skill/admin",
                )

    # -- Combined pre-run check ----------------------------------------------

    def enforce_all(
        self,
        binding: FieldBinding,
        artifact_id: str,
        *,
        auto_apply: bool = False,
        caller_role: str = "editor",
    ) -> None:
        """
        Run all policy checks in order:
          1. lock
          2. cooldown
          3. auto_apply (only if auto_apply=True)
        Raises the first applicable error.
        """
        self.enforce_lock(binding)
        self.check_cooldown(binding, artifact_id)
        if auto_apply:
            self.check_auto_apply(binding, caller_role)
