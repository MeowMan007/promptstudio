"""Tests for TSK-104, TSK-106, TSK-108, TSK-109, TSK-110 (observability + evals).

Covers:
  - evals/harness.py         (TSK-104 / TSK-106)
  - observability/tracer.py  (TSK-108)
  - observability/dashboards.py (TSK-109)
"""
import pytest
import time

from backend.app.evals.harness import (
    EvalCase,
    EvalDataset,
    Assertion,
    AssertionType,
    PromptEvalHarness,
    VersionScore,
    regression_gate,
    RegressionError,
    _evaluate_assertion,
)
from backend.app.observability.tracer import (
    PSTracer,
    SpanCollector,
    SpanStatus,
)
from backend.app.observability.dashboards import (
    PSMetrics,
    AlertRule,
    AlertOperator,
    AlertSeverity,
    evaluate_alert,
    DEFAULT_ALERT_RULES,
    DEFAULT_DASHBOARD_PANELS,
    DashboardPanel,
)


# ==========================================================================
# TSK-104: promptfoo harness + eval datasets
# ==========================================================================

class TestEvalHarness:

    def _dataset(self, cases=None) -> EvalDataset:
        if cases is None:
            cases = [
                EvalCase(
                    case_id="case-001",
                    prompt_id="greeting",
                    variables={"name": "Alice"},
                    assertions=[
                        Assertion(AssertionType.CONTAINS, "stub output"),
                    ],
                )
            ]
        return EvalDataset(
            dataset_id="ds-001",
            prompt_id="greeting",
            prompt_version=1,
            cases=cases,
        )

    def test_harness_runs_dataset(self):
        harness = PromptEvalHarness()
        result = harness.run_dataset(self._dataset())
        assert len(result.case_results) == 1

    def test_harness_overall_score_in_range(self):
        harness = PromptEvalHarness()
        result = harness.run_dataset(self._dataset())
        assert 0.0 <= result.overall_score <= 1.0

    def test_exact_match_passes(self):
        def runner(pid, ver, vars):
            return "Hello Alice"
        harness = PromptEvalHarness(runner=runner)
        cases = [EvalCase("c1", "p", {"name": "Alice"}, assertions=[
            Assertion(AssertionType.EXACT_MATCH, "Hello Alice"),
        ])]
        result = harness.run_dataset(EvalDataset("ds", "p", 1, cases))
        assert result.case_results[0].passed

    def test_exact_match_fails(self):
        def runner(pid, ver, vars):
            return "Hello Bob"
        harness = PromptEvalHarness(runner=runner)
        cases = [EvalCase("c1", "p", {}, assertions=[
            Assertion(AssertionType.EXACT_MATCH, "Hello Alice"),
        ])]
        result = harness.run_dataset(EvalDataset("ds", "p", 1, cases))
        assert not result.case_results[0].passed

    def test_contains_assertion(self):
        passed, score = _evaluate_assertion("Hello World!", Assertion(AssertionType.CONTAINS, "World"))
        assert passed
        assert score == 1.0

    def test_not_contains_assertion(self):
        passed, _ = _evaluate_assertion("Safe text", Assertion(AssertionType.NOT_CONTAINS, "secret"))
        assert passed

    def test_starts_with_assertion(self):
        passed, _ = _evaluate_assertion("BEGIN data", Assertion(AssertionType.STARTS_WITH, "BEGIN"))
        assert passed

    def test_ends_with_assertion(self):
        passed, _ = _evaluate_assertion("data END", Assertion(AssertionType.ENDS_WITH, "END"))
        assert passed

    def test_regex_assertion(self):
        passed, _ = _evaluate_assertion("Order #12345", Assertion(AssertionType.REGEX, r"#\d+"))
        assert passed

    def test_json_schema_assertion_valid(self):
        passed, _ = _evaluate_assertion('{"key": "value"}', Assertion(AssertionType.JSON_SCHEMA, None))
        assert passed

    def test_json_schema_assertion_invalid(self):
        passed, _ = _evaluate_assertion("not json", Assertion(AssertionType.JSON_SCHEMA, None))
        assert not passed

    def test_length_lte_assertion(self):
        passed, _ = _evaluate_assertion("short", Assertion(AssertionType.LENGTH_LTE, 10))
        assert passed

    def test_length_lte_fails_on_long(self):
        passed, _ = _evaluate_assertion("x" * 100, Assertion(AssertionType.LENGTH_LTE, 10))
        assert not passed

    def test_length_gte_assertion(self):
        passed, _ = _evaluate_assertion("x" * 50, Assertion(AssertionType.LENGTH_GTE, 10))
        assert passed

    def test_rubric_assertion_returns_neutral(self):
        passed, score = _evaluate_assertion("any output", Assertion(AssertionType.RUBRIC, "quality"))
        assert passed  # rubric is not blocking in CI
        assert score == 0.5  # neutral placeholder

    def test_deterministic_assertions_before_rubric(self):
        """Deterministic assertions must run first (spec 29.4)."""
        order: list[str] = []

        def runner(pid, ver, vars):
            return "Hello World"

        cases = [EvalCase("c1", "p", {}, assertions=[
            Assertion(AssertionType.RUBRIC, "quality"),
            Assertion(AssertionType.CONTAINS, "Hello"),
            Assertion(AssertionType.EXACT_MATCH, "Hello World"),
        ])]
        harness = PromptEvalHarness(runner=runner)
        result = harness.run_dataset(EvalDataset("ds", "p", 1, cases))
        ar = result.case_results[0].assertion_results
        # Rubric must be last
        assert ar[-1]["type"] == AssertionType.RUBRIC.value

    def test_overall_score_weighted(self):
        def runner(pid, ver, vars):
            return "Hello"
        harness = PromptEvalHarness(runner=runner, pass_threshold=0.5)
        cases = [EvalCase("c1", "p", {}, assertions=[
            Assertion(AssertionType.CONTAINS, "Hello", weight=2.0),
            Assertion(AssertionType.CONTAINS, "World", weight=1.0),  # will fail
        ])]
        result = harness.run_dataset(EvalDataset("ds", "p", 1, cases))
        # Hello passes (weight 2), World fails (weight 1) → score = 2/3 ≈ 0.667
        assert abs(result.case_results[0].score - 2/3) < 0.01

    def test_runner_exception_captured(self):
        def bad_runner(pid, ver, vars):
            raise RuntimeError("model unavailable")
        harness = PromptEvalHarness(runner=bad_runner)
        result = harness.run_dataset(self._dataset())
        assert result.case_results[0].error == "model unavailable"

    def test_empty_dataset_zero_score(self):
        harness = PromptEvalHarness()
        result = harness.run_dataset(EvalDataset("ds", "p", 1, cases=[]))
        assert result.overall_score == 0.0

    def test_pass_threshold_applied(self):
        def runner(pid, ver, vars):
            return "correct"
        harness = PromptEvalHarness(runner=runner, pass_threshold=0.9)
        cases = [EvalCase("c1", "p", {}, assertions=[
            Assertion(AssertionType.EXACT_MATCH, "wrong"),  # fails → score 0
        ])]
        result = harness.run_dataset(EvalDataset("ds", "p", 1, cases))
        assert not result.passed


# ==========================================================================
# TSK-106: Prompt regression gate
# ==========================================================================

class TestRegressionGate:

    def _score(self, version: int, score: float) -> VersionScore:
        return VersionScore("greeting", version, score, "ds-001")

    def test_improvement_passes(self):
        incumbent = self._score(1, 0.80)
        candidate = self._score(2, 0.85)
        regression_gate(incumbent, candidate)  # should not raise

    def test_small_regression_within_threshold_passes(self):
        incumbent = self._score(1, 0.80)
        candidate = self._score(2, 0.79)  # -0.01 within -0.02 threshold
        regression_gate(incumbent, candidate)  # should not raise

    def test_large_regression_raises(self):
        incumbent = self._score(1, 0.80)
        candidate = self._score(2, 0.70)  # -0.10 — too much
        with pytest.raises(RegressionError):
            regression_gate(incumbent, candidate)

    def test_exactly_at_threshold_passes(self):
        incumbent = self._score(1, 0.80)
        candidate = self._score(2, 0.78)  # -0.02 exactly at boundary
        regression_gate(incumbent, candidate)  # should not raise

    def test_just_below_threshold_raises(self):
        incumbent = self._score(1, 0.80)
        candidate = self._score(2, 0.779)  # -0.021 — just below
        with pytest.raises(RegressionError):
            regression_gate(incumbent, candidate)

    def test_prompt_id_mismatch_raises(self):
        incumbent = VersionScore("prompt-A", 1, 0.8, "ds-001")
        candidate = VersionScore("prompt-B", 2, 0.9, "ds-001")
        with pytest.raises(ValueError):
            regression_gate(incumbent, candidate)

    def test_zero_incumbent_score_allows_improvement(self):
        incumbent = self._score(1, 0.0)
        candidate = self._score(2, 0.5)
        regression_gate(incumbent, candidate)  # should not raise

    def test_regression_error_message_contains_versions(self):
        incumbent = self._score(1, 0.9)
        candidate = self._score(2, 0.5)
        with pytest.raises(RegressionError, match="v1"):
            regression_gate(incumbent, candidate)

    def test_custom_threshold(self):
        incumbent = self._score(1, 0.8)
        candidate = self._score(2, 0.75)  # -0.05
        # With stricter threshold (0), any drop fails
        with pytest.raises(RegressionError):
            regression_gate(incumbent, candidate, min_improvement=0.0)

    def test_custom_threshold_allows_larger_drop(self):
        incumbent = self._score(1, 0.8)
        candidate = self._score(2, 0.70)  # -0.10
        # Very permissive threshold
        regression_gate(incumbent, candidate, min_improvement=-0.15)  # should not raise


# ==========================================================================
# TSK-108: OTel tracing
# ==========================================================================

class TestOTelTracing:

    def _tracer(self) -> PSTracer:
        collector = SpanCollector()
        return PSTracer("test-service", collector)

    def test_span_recorded(self):
        tracer = self._tracer()
        with tracer.start_span("my.span") as span:
            pass
        spans = tracer.collector().spans()
        assert len(spans) == 1
        assert spans[0].name == "my.span"

    def test_span_has_service_attribute(self):
        tracer = self._tracer()
        with tracer.start_span("test") as span:
            pass
        assert tracer.collector().spans()[0].attributes["service.name"] == "test-service"

    def test_span_status_ok_on_success(self):
        tracer = self._tracer()
        with tracer.start_span("ok.span") as span:
            pass
        assert tracer.collector().spans()[0].status == SpanStatus.OK

    def test_span_status_error_on_exception(self):
        tracer = self._tracer()
        with pytest.raises(ValueError):
            with tracer.start_span("err.span"):
                raise ValueError("boom")
        spans = tracer.collector().spans()
        assert spans[0].status == SpanStatus.ERROR

    def test_span_duration_ms_set(self):
        tracer = self._tracer()
        with tracer.start_span("timed"):
            time.sleep(0.001)
        span = tracer.collector().spans()[0]
        assert span.duration_ms is not None
        assert span.duration_ms >= 0.0

    def test_nested_spans_share_trace_id(self):
        tracer = self._tracer()
        with tracer.start_span("parent", new_trace=True):
            with tracer.start_span("child"):
                pass
        spans = tracer.collector().spans()
        assert len(spans) == 2
        assert spans[0].trace_id == spans[1].trace_id

    def test_child_has_parent_id(self):
        tracer = self._tracer()
        with tracer.start_span("parent", new_trace=True) as parent:
            with tracer.start_span("child") as child:
                pass
        spans = tracer.collector().spans_by_name("child")
        assert spans[0].parent_span_id is not None

    def test_model_call_attributes(self):
        tracer = self._tracer()
        with tracer.trace_model_call("gpt-4o", prompt_tokens=100, completion_tokens=50):
            pass
        spans = tracer.collector().spans_by_name("gen_ai.model_call")
        assert len(spans) == 1
        attr = spans[0].attributes
        assert attr["gen_ai.request.model"] == "gpt-4o"
        assert attr["gen_ai.usage.prompt_tokens"] == 100
        assert attr["gen_ai.usage.completion_tokens"] == 50

    def test_tool_call_attributes(self):
        tracer = self._tracer()
        with tracer.trace_tool_call("list_projects", caller_id="user-1"):
            pass
        spans = tracer.collector().spans_by_name("ps.tool_call")
        assert spans[0].attributes["ps.tool.name"] == "list_projects"
        assert spans[0].attributes["ps.tool.caller_id"] == "user-1"

    def test_patch_attributes(self):
        tracer = self._tracer()
        with tracer.trace_patch("patch-abc", artifact_id="art-1", operation_count=3):
            pass
        spans = tracer.collector().spans_by_name("ps.patch_apply")
        assert spans[0].attributes["ps.patch.id"] == "patch-abc"
        assert spans[0].attributes["ps.patch.operation_count"] == 3

    def test_export_attributes(self):
        tracer = self._tracer()
        with tracer.trace_export("job-1", format_name="zip", artifact_count=10):
            pass
        spans = tracer.collector().spans_by_name("ps.export")
        assert spans[0].attributes["ps.export.format"] == "zip"
        assert spans[0].attributes["ps.export.artifact_count"] == 10

    def test_prompt_run_attributes(self):
        tracer = self._tracer()
        with tracer.trace_prompt_run("run-1", prompt_id="greeting", version=2):
            pass
        spans = tracer.collector().spans_by_name("ps.prompt_run")
        assert spans[0].attributes["ps.prompt.id"] == "greeting"
        assert spans[0].attributes["ps.prompt.version"] == 2

    def test_full_run_spans_all_operations(self):
        """A full run spans model call, tool call, patch, and export (spec 30.2)."""
        tracer = self._tracer()
        with tracer.start_span("ps.full_run", new_trace=True):
            with tracer.trace_model_call("gpt-4o"):
                pass
            with tracer.trace_tool_call("list_projects", caller_id="agent"):
                pass
            with tracer.trace_patch("patch-1"):
                pass
            with tracer.trace_export("job-1"):
                pass

        spans = tracer.collector().spans()
        names = {s.name for s in spans}
        assert "gen_ai.model_call" in names
        assert "ps.tool_call" in names
        assert "ps.patch_apply" in names
        assert "ps.export" in names

    def test_find_by_attribute(self):
        tracer = self._tracer()
        with tracer.trace_tool_call("my_tool"):
            pass
        found = tracer.collector().find_by_attribute("ps.tool.name", "my_tool")
        assert len(found) == 1

    def test_span_add_event(self):
        tracer = self._tracer()
        with tracer.start_span("evented") as span:
            span.add_event("checkpoint", {"progress": 50})
        spans = tracer.collector().spans()
        assert len(spans[0].events) == 1
        assert spans[0].events[0]["name"] == "checkpoint"

    def test_collector_clear(self):
        tracer = self._tracer()
        with tracer.start_span("test"):
            pass
        tracer.collector().clear()
        assert tracer.collector().spans() == []


# ==========================================================================
# TSK-109: Dashboards and alerts
# ==========================================================================

class TestDashboardsAndAlerts:

    def test_all_metrics_have_names(self):
        for metric in PSMetrics.ALL:
            assert metric.name.startswith("ps.")

    def test_all_key_signals_present(self):
        """All 30.3 signals have metric definitions."""
        names = {m.name for m in PSMetrics.ALL}
        required = {
            "ps.prompt.run.total",
            "ps.prompt.run.duration_ms",
            "ps.tool.call.total",
            "ps.patch.apply.total",
            "ps.export.job.total",
            "ps.export.secrets_detected.total",
            "ps.agency.kill_switch.total",
            "ps.agency.budget_exceeded.total",
        }
        missing = required - names
        assert missing == set(), f"Missing metric definitions: {missing}"

    def test_default_alert_rules_non_empty(self):
        assert len(DEFAULT_ALERT_RULES) > 0

    def test_alert_rules_have_required_fields(self):
        for rule in DEFAULT_ALERT_RULES:
            assert rule.name
            assert rule.metric is not None
            assert rule.severity in AlertSeverity.__members__.values()

    def test_evaluate_alert_gt_triggers(self):
        rule = AlertRule(
            name="test",
            metric=PSMetrics.PROMPT_RUN_TOTAL,
            operator=AlertOperator.GT,
            threshold=10,
            severity=AlertSeverity.WARNING,
        )
        assert evaluate_alert(rule, 11.0)
        assert not evaluate_alert(rule, 9.0)
        assert not evaluate_alert(rule, 10.0)

    def test_evaluate_alert_gte_triggers(self):
        rule = AlertRule("r", PSMetrics.KILL_SWITCH_ACTIVATIONS, AlertOperator.GTE, 1, AlertSeverity.CRITICAL)
        assert evaluate_alert(rule, 1.0)
        assert evaluate_alert(rule, 2.0)
        assert not evaluate_alert(rule, 0.5)

    def test_evaluate_alert_lt_triggers(self):
        rule = AlertRule("r", PSMetrics.PROMPT_RUN_TOTAL, AlertOperator.LT, 5, AlertSeverity.INFO)
        assert evaluate_alert(rule, 3.0)
        assert not evaluate_alert(rule, 5.0)
        assert not evaluate_alert(rule, 6.0)

    def test_kill_switch_alert_critical(self):
        """Kill switch must be a critical alert."""
        kill_rules = [r for r in DEFAULT_ALERT_RULES if "KillSwitch" in r.name]
        assert len(kill_rules) > 0
        assert all(r.severity == AlertSeverity.CRITICAL for r in kill_rules)

    def test_secret_detection_alert_critical(self):
        """Secret detection must be critical."""
        secret_rules = [r for r in DEFAULT_ALERT_RULES if "Secret" in r.name]
        assert len(secret_rules) > 0
        assert all(r.severity == AlertSeverity.CRITICAL for r in secret_rules)

    def test_default_dashboard_panels_cover_all_signals(self):
        panel_metrics = {p.metric.name for p in DEFAULT_DASHBOARD_PANELS}
        required = {
            "ps.prompt.run.total",
            "ps.tool.call.total",
            "ps.export.job.total",
            "ps.agency.kill_switch.total",
            "ps.export.secrets_detected.total",
        }
        missing = required - panel_metrics
        assert missing == set(), f"Missing dashboard panels: {missing}"

    def test_default_dashboard_has_all_key_panel_types(self):
        from backend.app.observability.dashboards import PanelType
        panel_types = {p.panel_type for p in DEFAULT_DASHBOARD_PANELS}
        assert PanelType.TIME_SERIES in panel_types
        assert PanelType.STAT in panel_types

    def test_metrics_all_list_non_empty(self):
        assert len(PSMetrics.ALL) >= 10

    def test_alert_rule_for_duration_non_negative(self):
        for rule in DEFAULT_ALERT_RULES:
            assert rule.for_duration_seconds >= 0

    def test_all_alert_metrics_in_metrics_all(self):
        """Every alert rule references a known metric."""
        known = {m.name for m in PSMetrics.ALL}
        for rule in DEFAULT_ALERT_RULES:
            assert rule.metric.name in known, \
                f"Alert {rule.name!r} references unknown metric {rule.metric.name!r}"
