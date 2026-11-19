"""
Tests for TSK-046: Field locks, cooldowns and per-binding policy enforcement.

Acceptance: Locked field rejects agent write; cooldown enforced; auto_apply restricted.
"""
from __future__ import annotations

import pytest

from backend.app.bindings.models import (
    AutoApplyPolicy,
    BindingPolicy,
    BindingScope,
    ContextRule,
    FieldBinding,
)
from backend.app.bindings.policy import (
    AutoApplyDeniedError,
    CooldownError,
    FieldLockError,
    PolicyEnforcer,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_binding(
    bid: str = "b1",
    *,
    locked: bool = False,
    cooldown: int = 0,
    auto_apply: AutoApplyPolicy = AutoApplyPolicy.NEVER,
) -> FieldBinding:
    return FieldBinding(
        id=bid,
        artifact_type="user_story",
        field_path="body",
        scope=BindingScope.TYPE_DEFAULT,
        scope_id="*",
        prompt_asset_id="pa1",
        policy=BindingPolicy(
            locked=locked,
            cooldown_seconds=cooldown,
            auto_apply=auto_apply,
        ),
    )


class FakeClock:
    """Controllable clock for deterministic cooldown tests."""
    def __init__(self, start: float = 0.0):
        self.t = start

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


# ---------------------------------------------------------------------------
# Lock tests
# ---------------------------------------------------------------------------

class TestFieldLock:
    def test_locked_binding_raises(self):
        enforcer = PolicyEnforcer()
        b = _make_binding(locked=True)
        with pytest.raises(FieldLockError) as exc_info:
            enforcer.enforce_lock(b)
        assert exc_info.value.binding_id == "b1"
        assert exc_info.value.field_path == "body"

    def test_unlocked_binding_ok(self):
        enforcer = PolicyEnforcer()
        b = _make_binding(locked=False)
        enforcer.enforce_lock(b)   # should not raise

    def test_lock_error_to_dict(self):
        err = FieldLockError("body", "b1")
        d = err.to_dict()
        assert d["code"] == "FIELD_LOCKED"
        assert d["field_path"] == "body"
        assert d["binding_id"] == "b1"


# ---------------------------------------------------------------------------
# Cooldown tests
# ---------------------------------------------------------------------------

class TestCooldown:
    def test_no_cooldown_ok(self):
        clock = FakeClock(0.0)
        enforcer = PolicyEnforcer(_clock=clock)
        b = _make_binding(cooldown=0)
        enforcer.check_cooldown(b, "art1")   # no-op

    def test_first_run_no_cooldown(self):
        clock = FakeClock(0.0)
        enforcer = PolicyEnforcer(_clock=clock)
        b = _make_binding(cooldown=30)
        enforcer.check_cooldown(b, "art1")   # no previous run → ok

    def test_cooldown_active_after_run(self):
        clock = FakeClock(100.0)
        enforcer = PolicyEnforcer(_clock=clock)
        b = _make_binding(cooldown=30)
        enforcer.record_run(b, "art1")
        clock.advance(10.0)   # only 10s elapsed, cooldown is 30s
        with pytest.raises(CooldownError) as exc_info:
            enforcer.check_cooldown(b, "art1")
        assert exc_info.value.remaining_seconds > 0

    def test_cooldown_expired_after_wait(self):
        clock = FakeClock(100.0)
        enforcer = PolicyEnforcer(_clock=clock)
        b = _make_binding(cooldown=30)
        enforcer.record_run(b, "art1")
        clock.advance(31.0)   # cooldown expired
        enforcer.check_cooldown(b, "art1")   # should not raise

    def test_cooldown_independent_per_artifact(self):
        clock = FakeClock(0.0)
        enforcer = PolicyEnforcer(_clock=clock)
        b = _make_binding(cooldown=30)
        enforcer.record_run(b, "art1")
        clock.advance(5.0)
        # art2 never ran — should be fine
        enforcer.check_cooldown(b, "art2")   # no raise

    def test_cooldown_error_to_dict(self):
        err = CooldownError("b1", 15.5)
        d = err.to_dict()
        assert d["code"] == "COOLDOWN_ACTIVE"
        assert d["binding_id"] == "b1"
        assert d["remaining_seconds"] == 15.5


# ---------------------------------------------------------------------------
# Auto-apply tests
# ---------------------------------------------------------------------------

class TestAutoApply:
    def test_never_policy_always_denied(self):
        enforcer = PolicyEnforcer()
        b = _make_binding(auto_apply=AutoApplyPolicy.NEVER)
        with pytest.raises(AutoApplyDeniedError):
            enforcer.check_auto_apply(b, "editor")

    def test_low_risk_allowed_for_editor(self):
        enforcer = PolicyEnforcer()
        b = _make_binding(auto_apply=AutoApplyPolicy.LOW_RISK)
        enforcer.check_auto_apply(b, "editor")   # ok

    def test_low_risk_denied_for_viewer(self):
        enforcer = PolicyEnforcer()
        b = _make_binding(auto_apply=AutoApplyPolicy.LOW_RISK)
        with pytest.raises(AutoApplyDeniedError):
            enforcer.check_auto_apply(b, "viewer")

    def test_always_policy_denied_for_editor(self):
        enforcer = PolicyEnforcer()
        b = _make_binding(auto_apply=AutoApplyPolicy.ALWAYS)
        with pytest.raises(AutoApplyDeniedError):
            enforcer.check_auto_apply(b, "editor")

    def test_always_policy_allowed_for_trusted_skill(self):
        enforcer = PolicyEnforcer()
        b = _make_binding(auto_apply=AutoApplyPolicy.ALWAYS)
        enforcer.check_auto_apply(b, "trusted_skill")   # ok

    def test_always_policy_allowed_for_admin(self):
        enforcer = PolicyEnforcer()
        b = _make_binding(auto_apply=AutoApplyPolicy.ALWAYS)
        enforcer.check_auto_apply(b, "admin")   # ok

    def test_auto_apply_denied_to_dict(self):
        err = AutoApplyDeniedError("b1", "policy is NEVER")
        d = err.to_dict()
        assert d["code"] == "AUTO_APPLY_DENIED"


# ---------------------------------------------------------------------------
# Combined enforce_all
# ---------------------------------------------------------------------------

class TestEnforceAll:
    def test_lock_checked_first(self):
        enforcer = PolicyEnforcer()
        b = _make_binding(locked=True, cooldown=30)
        with pytest.raises(FieldLockError):
            enforcer.enforce_all(b, "art1")

    def test_cooldown_checked_after_lock(self):
        clock = FakeClock(0.0)
        enforcer = PolicyEnforcer(_clock=clock)
        b = _make_binding(cooldown=30)
        enforcer.record_run(b, "art1")
        clock.advance(5.0)
        with pytest.raises(CooldownError):
            enforcer.enforce_all(b, "art1")

    def test_auto_apply_only_checked_when_flagged(self):
        enforcer = PolicyEnforcer()
        b = _make_binding(auto_apply=AutoApplyPolicy.NEVER)
        # Without auto_apply=True flag → no AutoApplyDeniedError
        enforcer.enforce_all(b, "art1", auto_apply=False)

    def test_auto_apply_denied_when_flagged(self):
        enforcer = PolicyEnforcer()
        b = _make_binding(auto_apply=AutoApplyPolicy.NEVER)
        with pytest.raises(AutoApplyDeniedError):
            enforcer.enforce_all(b, "art1", auto_apply=True, caller_role="editor")
