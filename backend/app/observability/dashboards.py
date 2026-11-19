"""TSK-109: Dashboards and alerts signal definitions.

Implements spec section 30.3:
  - AlertRule: threshold-based alert definition
  - DashboardPanel: a panel specification for a monitoring dashboard
  - PSMetrics: canonical metric names with their signal types
  - evaluate_alert(): check if a metric value triggers an alert
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Metric / Signal definitions
# ---------------------------------------------------------------------------

class MetricType(str, Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertOperator(str, Enum):
    GT = ">"    # greater than
    GTE = ">="
    LT = "<"
    LTE = "<="
    EQ = "=="
    NEQ = "!="


@dataclass
class MetricDefinition:
    name: str
    metric_type: MetricType
    description: str
    unit: str = ""
    labels: list[str] = field(default_factory=list)


# Canonical Prompt Studio metrics (spec 30.3)
class PSMetrics:
    """All signals that must have dashboards and alert rules per spec 30.3."""

    # Prompt runs
    PROMPT_RUN_TOTAL = MetricDefinition(
        "ps.prompt.run.total", MetricType.COUNTER,
        "Total prompt runs", labels=["prompt_id", "version", "status"]
    )
    PROMPT_RUN_DURATION_MS = MetricDefinition(
        "ps.prompt.run.duration_ms", MetricType.HISTOGRAM,
        "Prompt run duration", unit="ms", labels=["prompt_id", "model"]
    )
    PROMPT_TOKEN_USAGE = MetricDefinition(
        "ps.prompt.tokens.total", MetricType.COUNTER,
        "Total tokens used", labels=["prompt_id", "model", "token_type"]
    )

    # Patch engine
    PATCH_APPLY_TOTAL = MetricDefinition(
        "ps.patch.apply.total", MetricType.COUNTER,
        "Total patches applied", labels=["artifact_type", "status"]
    )
    PATCH_REJECT_TOTAL = MetricDefinition(
        "ps.patch.reject.total", MetricType.COUNTER,
        "Total patches rejected", labels=["reason"]
    )

    # Tool router
    TOOL_CALL_TOTAL = MetricDefinition(
        "ps.tool.call.total", MetricType.COUNTER,
        "Total tool calls", labels=["tool_name", "class", "status"]
    )
    TOOL_CALL_DURATION_MS = MetricDefinition(
        "ps.tool.call.duration_ms", MetricType.HISTOGRAM,
        "Tool call duration", unit="ms", labels=["tool_name"]
    )

    # Export pipeline
    EXPORT_JOB_TOTAL = MetricDefinition(
        "ps.export.job.total", MetricType.COUNTER,
        "Total export jobs", labels=["format", "status"]
    )
    EXPORT_SECRET_DETECTIONS = MetricDefinition(
        "ps.export.secrets_detected.total", MetricType.COUNTER,
        "Secret detections during export scan", labels=["pattern_type"]
    )

    # Agency controls
    BUDGET_EXCEEDED_TOTAL = MetricDefinition(
        "ps.agency.budget_exceeded.total", MetricType.COUNTER,
        "Times budget cap was hit", labels=["cap_type"]
    )
    KILL_SWITCH_ACTIVATIONS = MetricDefinition(
        "ps.agency.kill_switch.total", MetricType.COUNTER,
        "Kill switch activations", labels=["reason"]
    )

    # Skill install
    SKILL_INSTALL_TOTAL = MetricDefinition(
        "ps.skill.install.total", MetricType.COUNTER,
        "Skill package installs", labels=["trust_level", "status"]
    )

    ALL: list[MetricDefinition] = []  # populated below


# Populate ALL list
PSMetrics.ALL = [
    v for v in vars(PSMetrics).values()
    if isinstance(v, MetricDefinition)
]


# ---------------------------------------------------------------------------
# Alert rules
# ---------------------------------------------------------------------------

@dataclass
class AlertRule:
    name: str
    metric: MetricDefinition
    operator: AlertOperator
    threshold: float
    severity: AlertSeverity
    description: str = ""
    for_duration_seconds: float = 60.0  # must be true for this long before firing
    labels_filter: dict[str, str] = field(default_factory=dict)


# Default alert rules covering spec 30.3
DEFAULT_ALERT_RULES: list[AlertRule] = [
    AlertRule(
        name="HighPromptRunErrorRate",
        metric=PSMetrics.PROMPT_RUN_TOTAL,
        operator=AlertOperator.GT,
        threshold=0.1,   # error rate > 10%
        severity=AlertSeverity.WARNING,
        description="Prompt run error rate exceeds 10% over 5 minutes",
        for_duration_seconds=300,
        labels_filter={"status": "error"},
    ),
    AlertRule(
        name="PromptRunLatencyHigh",
        metric=PSMetrics.PROMPT_RUN_DURATION_MS,
        operator=AlertOperator.GT,
        threshold=10_000,  # > 10 seconds p99
        severity=AlertSeverity.WARNING,
        description="p99 prompt run latency exceeds 10s",
        for_duration_seconds=120,
    ),
    AlertRule(
        name="KillSwitchActivated",
        metric=PSMetrics.KILL_SWITCH_ACTIVATIONS,
        operator=AlertOperator.GTE,
        threshold=1,
        severity=AlertSeverity.CRITICAL,
        description="Agency kill switch was activated",
        for_duration_seconds=0,
    ),
    AlertRule(
        name="SecretDetectedInExport",
        metric=PSMetrics.EXPORT_SECRET_DETECTIONS,
        operator=AlertOperator.GTE,
        threshold=1,
        severity=AlertSeverity.CRITICAL,
        description="Secret pattern detected during export scan",
        for_duration_seconds=0,
    ),
    AlertRule(
        name="BudgetExceeded",
        metric=PSMetrics.BUDGET_EXCEEDED_TOTAL,
        operator=AlertOperator.GTE,
        threshold=1,
        severity=AlertSeverity.WARNING,
        description="Agency cost or call budget was exceeded",
        for_duration_seconds=0,
    ),
    AlertRule(
        name="PatchRejectionSpike",
        metric=PSMetrics.PATCH_REJECT_TOTAL,
        operator=AlertOperator.GT,
        threshold=5,
        severity=AlertSeverity.WARNING,
        description="More than 5 patch rejections in 5 minutes",
        for_duration_seconds=300,
    ),
]


# ---------------------------------------------------------------------------
# Alert evaluation
# ---------------------------------------------------------------------------

_OPS: dict[AlertOperator, Any] = {
    AlertOperator.GT: lambda v, t: v > t,
    AlertOperator.GTE: lambda v, t: v >= t,
    AlertOperator.LT: lambda v, t: v < t,
    AlertOperator.LTE: lambda v, t: v <= t,
    AlertOperator.EQ: lambda v, t: v == t,
    AlertOperator.NEQ: lambda v, t: v != t,
}


def evaluate_alert(rule: AlertRule, current_value: float) -> bool:
    """Return True if the current metric value triggers the alert rule."""
    op_fn = _OPS[rule.operator]
    return op_fn(current_value, rule.threshold)


# ---------------------------------------------------------------------------
# Dashboard panel definitions
# ---------------------------------------------------------------------------

class PanelType(str, Enum):
    TIME_SERIES = "time_series"
    STAT = "stat"
    TABLE = "table"
    PIE = "pie"
    GAUGE = "gauge_panel"


@dataclass
class DashboardPanel:
    title: str
    panel_type: PanelType
    metric: MetricDefinition
    description: str = ""
    aggregation: str = "sum"   # sum | rate | avg | p99
    group_by: list[str] = field(default_factory=list)


# Default dashboard: one panel per key signal
DEFAULT_DASHBOARD_PANELS: list[DashboardPanel] = [
    DashboardPanel("Prompt Run Rate", PanelType.TIME_SERIES, PSMetrics.PROMPT_RUN_TOTAL,
                   aggregation="rate", group_by=["status"]),
    DashboardPanel("Prompt Latency p99", PanelType.TIME_SERIES, PSMetrics.PROMPT_RUN_DURATION_MS,
                   aggregation="p99"),
    DashboardPanel("Token Usage", PanelType.TIME_SERIES, PSMetrics.PROMPT_TOKEN_USAGE,
                   aggregation="sum", group_by=["model"]),
    DashboardPanel("Tool Calls", PanelType.TIME_SERIES, PSMetrics.TOOL_CALL_TOTAL,
                   aggregation="rate", group_by=["tool_name", "status"]),
    DashboardPanel("Patch Apply Rate", PanelType.TIME_SERIES, PSMetrics.PATCH_APPLY_TOTAL,
                   aggregation="rate", group_by=["status"]),
    DashboardPanel("Export Jobs", PanelType.STAT, PSMetrics.EXPORT_JOB_TOTAL,
                   aggregation="sum", group_by=["status"]),
    DashboardPanel("Secret Detections", PanelType.STAT, PSMetrics.EXPORT_SECRET_DETECTIONS,
                   aggregation="sum"),
    DashboardPanel("Kill Switch Events", PanelType.STAT, PSMetrics.KILL_SWITCH_ACTIVATIONS,
                   aggregation="sum"),
    DashboardPanel("Budget Exceeded Events", PanelType.STAT, PSMetrics.BUDGET_EXCEEDED_TOTAL,
                   aggregation="sum"),
    DashboardPanel("Skill Installs", PanelType.PIE, PSMetrics.SKILL_INSTALL_TOTAL,
                   aggregation="sum", group_by=["trust_level"]),
]
