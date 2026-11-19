"""TSK-108: OpenTelemetry tracing with GenAI + ps.* attributes.

Implements spec section 30.2:
  - Tracer that spans a full run including tool calls, patch, and export
  - GenAI semantic conventions: gen_ai.* attributes
  - Prompt Studio custom attributes: ps.*
  - In-memory SpanCollector for testing (no OTLP required)
"""
from __future__ import annotations

import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Generator


# ---------------------------------------------------------------------------
# Span / Trace data models
# ---------------------------------------------------------------------------

class SpanStatus(str, Enum):
    OK = "OK"
    ERROR = "ERROR"
    UNSET = "UNSET"


@dataclass
class Span:
    """A single trace span."""
    trace_id: str
    span_id: str
    parent_span_id: str | None
    name: str
    start_time: float
    end_time: float | None = None
    status: SpanStatus = SpanStatus.UNSET
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)

    @property
    def duration_ms(self) -> float | None:
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time) * 1000

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        self.events.append({
            "name": name,
            "timestamp": time.monotonic(),
            "attributes": attributes or {},
        })

    def set_status(self, status: SpanStatus, message: str = "") -> None:
        self.status = status
        if message:
            self.attributes["status.message"] = message

    def end(self) -> None:
        if self.end_time is None:
            self.end_time = time.monotonic()


# ---------------------------------------------------------------------------
# Span collector (in-memory exporter for tests)
# ---------------------------------------------------------------------------

class SpanCollector:
    """In-memory span collector — replaces OTLP exporter in tests."""

    def __init__(self) -> None:
        self._spans: list[Span] = []

    def record(self, span: Span) -> None:
        self._spans.append(span)

    def spans(self) -> list[Span]:
        return list(self._spans)

    def spans_by_name(self, name: str) -> list[Span]:
        return [s for s in self._spans if s.name == name]

    def clear(self) -> None:
        self._spans.clear()

    def find_by_attribute(self, key: str, value: Any) -> list[Span]:
        return [s for s in self._spans if s.attributes.get(key) == value]


# ---------------------------------------------------------------------------
# Tracer
# ---------------------------------------------------------------------------

class PSTracer:
    """Prompt Studio tracer.

    Wraps span lifecycle and injects GenAI + ps.* semantic attributes.
    Compatible with OpenTelemetry API surface (can be backed by OTLP).
    """

    def __init__(
        self,
        service_name: str = "prompt-studio",
        collector: SpanCollector | None = None,
    ) -> None:
        self.service_name = service_name
        self._collector = collector or SpanCollector()
        self._active_trace_id: str | None = None
        self._active_span_id: str | None = None

    def _new_id(self) -> str:
        return uuid.uuid4().hex[:16]

    def _new_trace_id(self) -> str:
        return uuid.uuid4().hex[:32]

    @contextmanager
    def start_span(
        self,
        name: str,
        attributes: dict[str, Any] | None = None,
        new_trace: bool = False,
    ) -> Generator[Span, None, None]:
        """Context manager that creates, yields, and closes a span."""
        trace_id = self._new_trace_id() if new_trace or not self._active_trace_id \
            else self._active_trace_id
        parent_id = None if new_trace else self._active_span_id
        span_id = self._new_id()

        span = Span(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_id,
            name=name,
            start_time=time.monotonic(),
            attributes={
                "service.name": self.service_name,
                **(attributes or {}),
            },
        )

        prev_trace = self._active_trace_id
        prev_span = self._active_span_id
        self._active_trace_id = trace_id
        self._active_span_id = span_id

        try:
            yield span
            if span.status == SpanStatus.UNSET:
                span.set_status(SpanStatus.OK)
        except Exception as exc:
            span.set_status(SpanStatus.ERROR, str(exc))
            span.add_event("exception", {"exception.message": str(exc), "exception.type": type(exc).__name__})
            raise
        finally:
            span.end()
            self._collector.record(span)
            self._active_trace_id = prev_trace
            self._active_span_id = prev_span

    # ------------------------------------------------------------------
    # GenAI semantic conventions (spec 30.2)
    # ------------------------------------------------------------------

    @contextmanager
    def trace_model_call(
        self,
        model: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        **extra_attrs: Any,
    ) -> Generator[Span, None, None]:
        """Trace a GenAI model call with gen_ai.* attributes."""
        attrs = {
            "gen_ai.system": "prompt_studio",
            "gen_ai.request.model": model,
            "gen_ai.usage.prompt_tokens": prompt_tokens,
            "gen_ai.usage.completion_tokens": completion_tokens,
            **extra_attrs,
        }
        with self.start_span("gen_ai.model_call", attributes=attrs) as span:
            yield span

    @contextmanager
    def trace_tool_call(
        self,
        tool_name: str,
        caller_id: str = "",
        **extra_attrs: Any,
    ) -> Generator[Span, None, None]:
        """Trace a tool call with ps.tool.* attributes."""
        attrs = {
            "ps.tool.name": tool_name,
            "ps.tool.caller_id": caller_id,
            **extra_attrs,
        }
        with self.start_span("ps.tool_call", attributes=attrs) as span:
            yield span

    @contextmanager
    def trace_patch(
        self,
        patch_id: str,
        artifact_id: str = "",
        operation_count: int = 0,
        **extra_attrs: Any,
    ) -> Generator[Span, None, None]:
        """Trace a patch apply with ps.patch.* attributes."""
        attrs = {
            "ps.patch.id": patch_id,
            "ps.patch.artifact_id": artifact_id,
            "ps.patch.operation_count": operation_count,
            **extra_attrs,
        }
        with self.start_span("ps.patch_apply", attributes=attrs) as span:
            yield span

    @contextmanager
    def trace_export(
        self,
        job_id: str,
        format_name: str = "",
        artifact_count: int = 0,
        **extra_attrs: Any,
    ) -> Generator[Span, None, None]:
        """Trace an export job with ps.export.* attributes."""
        attrs = {
            "ps.export.job_id": job_id,
            "ps.export.format": format_name,
            "ps.export.artifact_count": artifact_count,
            **extra_attrs,
        }
        with self.start_span("ps.export", attributes=attrs) as span:
            yield span

    @contextmanager
    def trace_prompt_run(
        self,
        run_id: str,
        prompt_id: str = "",
        version: int = 0,
        **extra_attrs: Any,
    ) -> Generator[Span, None, None]:
        """Trace a prompt run with ps.prompt.* attributes."""
        attrs = {
            "ps.prompt.run_id": run_id,
            "ps.prompt.id": prompt_id,
            "ps.prompt.version": version,
            **extra_attrs,
        }
        with self.start_span("ps.prompt_run", attributes=attrs) as span:
            yield span

    def collector(self) -> SpanCollector:
        return self._collector
