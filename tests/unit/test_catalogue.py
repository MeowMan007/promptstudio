"""
Tests for TSK-044: Built-in field prompt catalogue (14 bindings).

Acceptance: Each binding has schema, eval cases and a passing smoke test.
"""
from __future__ import annotations

import pytest

from backend.app.bindings.catalogue import CATALOGUE, get_binding, smoke_test_binding
from backend.app.bindings.models import BindingScope


class TestCatalogueSize:
    def test_exactly_14_bindings(self):
        assert len(CATALOGUE) == 14

    def test_all_ids_unique(self):
        ids = [b.id for b in CATALOGUE]
        assert len(ids) == len(set(ids))

    def test_all_ids_start_with_builtin(self):
        for b in CATALOGUE:
            assert b.id.startswith("builtin:"), f"{b.id} should start with 'builtin:'"


class TestCatalogueContents:
    def test_all_at_type_default_scope(self):
        for b in CATALOGUE:
            assert b.scope == BindingScope.TYPE_DEFAULT, f"{b.id} should be TYPE_DEFAULT"

    def test_all_have_prompt_asset_id(self):
        for b in CATALOGUE:
            assert b.prompt_asset_id, f"{b.id} missing prompt_asset_id"

    def test_all_have_max_tokens_positive(self):
        for b in CATALOGUE:
            assert b.context_rule.max_tokens > 0, f"{b.id} max_tokens <= 0"

    def test_all_have_valid_schema_type(self):
        valid = {"string", "array", "object"}
        for b in CATALOGUE:
            schema_type = b.output_contract.json_schema.get("type")
            assert schema_type in valid, f"{b.id} schema type {schema_type!r} not in {valid}"

    def test_smoke_test_all_pass(self):
        """Acceptance: each binding passes its smoke test."""
        for b in CATALOGUE:
            failures = smoke_test_binding(b)
            assert failures == [], f"Binding {b.id} failed smoke: {failures}"


class TestGetBinding:
    def test_lookup_known_binding(self):
        b = get_binding("user_story", "body")
        assert b is not None
        assert b.id == "builtin:user_story:body"

    def test_lookup_acceptance_criteria(self):
        b = get_binding("user_story", "payload.acceptance_criteria")
        assert b is not None
        assert b.output_contract.json_schema.get("type") == "array"

    def test_lookup_missing_returns_none(self):
        assert get_binding("nonexistent_type", "body") is None

    def test_lookup_brief_body(self):
        b = get_binding("brief", "body")
        assert b is not None
        assert "idea" in b.context_rule.include_sibling_types or "problem" in b.context_rule.include_sibling_types

    def test_lookup_test_case_has_cooldown(self):
        b = get_binding("test_case", "body")
        assert b is not None
        assert b.policy.cooldown_seconds > 0

    def test_lookup_user_story_has_cooldown(self):
        b = get_binding("user_story", "body")
        assert b is not None
        assert b.policy.cooldown_seconds > 0

    def test_all_14_types_lookable(self):
        expected_pairs = [
            ("brief", "body"),
            ("persona", "body"),
            ("user_story", "body"),
            ("user_story", "payload.acceptance_criteria"),
            ("requirement", "body"),
            ("constraint", "body"),
            ("decision", "body"),
            ("user_flow", "body"),
            ("screen", "body"),
            ("api_endpoint", "body"),
            ("data_entity", "body"),
            ("risk", "body"),
            ("test_case", "body"),
            ("evaluation_case", "body"),
        ]
        for atype, fpath in expected_pairs:
            b = get_binding(atype, fpath)
            assert b is not None, f"Missing built-in binding for ({atype}, {fpath})"


class TestSmokeTestHelper:
    def test_smoke_pass_on_valid_binding(self):
        b = get_binding("brief", "body")
        assert b is not None
        failures = smoke_test_binding(b)
        assert failures == []

    def test_smoke_detects_missing_id(self):
        from backend.app.bindings.models import FieldBinding
        from backend.app.bindings.catalogue import _b
        b = get_binding("persona", "body")
        assert b is not None
        import copy
        bad = copy.deepcopy(b)
        bad.id = ""
        failures = smoke_test_binding(bad)
        assert any("id" in f for f in failures)
