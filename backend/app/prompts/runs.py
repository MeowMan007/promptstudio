"""
TSK-071: Prompt runs with DNA pinning and usage accounting.
TSK-073: Evaluation cases, runs, and comparison.

A PromptRun captures everything needed to reproduce or audit a model call:
  - The exact PromptVersion (pinned by version_id + content_hash)
  - The exact variable values used (DNA pinning)
  - Token cost + trace ID

An EvaluationCase defines expected behavior;
An EvaluationRun scores a PromptRun against one or more EvaluationCases.

Acceptance (TSK-071): Re-run uses pinned inputs; cost/tokens recorded; trace linked.
Acceptance (TSK-073): Side-by-side on same dataset; per-case pass/fail; rubric scores.
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from backend.app.prompts.assets import PromptVersion, render_prompt


# =============================================================================
# TSK-071: Prompt runs + DNA pinning
# =============================================================================

@dataclass
class PromptRunInputs:
    """
    Pinned snapshot of everything used to call the model.
    Stored verbatim so the run can be reproduced exactly.
    """
    version_id: str
    version_hash: str           # content_hash of the PromptVersion
    variable_values: dict[str, str]
    rendered_prompt: str        # the final rendered string sent to model
    input_hash: str             # sha256 of rendered_prompt (DNA pin)


@dataclass
class PromptRun:
    """
    One recorded model call against a PromptVersion.
    """
    run_id: str
    asset_id: str
    inputs: PromptRunInputs
    provider: str
    model_name: str
    raw_output: str
    tokens_input: int
    tokens_output: int
    cost_usd: float
    trace_id: str
    created_at: float = field(default_factory=time.monotonic)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        return self.tokens_input + self.tokens_output


def _pin_hash(rendered: str) -> str:
    return f"sha256:{hashlib.sha256(rendered.encode()).hexdigest()}"


def create_prompt_run(
    *,
    run_id: str,
    version: PromptVersion,
    variable_values: dict[str, str],
    provider: str = "stub",
    model_name: str = "stub-model",
    raw_output: str = "",
    tokens_input: int = 0,
    tokens_output: int = 0,
    cost_usd: float = 0.0,
    metadata: dict[str, Any] | None = None,
) -> PromptRun:
    """
    Create a PromptRun with pinned inputs.
    Automatically renders the prompt and computes the DNA pin hash.
    """
    rendered = render_prompt(version, variable_values, allow_missing=True)
    pin = _pin_hash(rendered)
    trace_id = f"trace:{hashlib.sha256(f'{run_id}:{pin}'.encode()).hexdigest()[:16]}"

    # Estimate tokens from chars if not provided
    if tokens_input == 0:
        tokens_input = max(1, len(rendered) // 4)
    if tokens_output == 0:
        tokens_output = max(1, len(raw_output) // 4)

    inputs = PromptRunInputs(
        version_id=version.version_id,
        version_hash=version.content_hash,
        variable_values=dict(variable_values),
        rendered_prompt=rendered,
        input_hash=pin,
    )

    return PromptRun(
        run_id=run_id,
        asset_id=version.asset_id,
        inputs=inputs,
        provider=provider,
        model_name=model_name,
        raw_output=raw_output,
        tokens_input=tokens_input,
        tokens_output=tokens_output,
        cost_usd=cost_usd,
        trace_id=trace_id,
        metadata=metadata or {},
    )


def rerun_from_pinned(
    original_run: PromptRun,
    *,
    new_run_id: str,
    version: PromptVersion,
    new_output: str = "",
) -> PromptRun:
    """
    Re-run using the exact pinned inputs from a previous run.
    Verifies the version hash matches before proceeding.
    """
    if version.content_hash != original_run.inputs.version_hash:
        raise ValueError(
            f"Version hash mismatch: original run used {original_run.inputs.version_hash!r}, "
            f"but provided version has {version.content_hash!r}"
        )
    return create_prompt_run(
        run_id=new_run_id,
        version=version,
        variable_values=original_run.inputs.variable_values,
        provider=original_run.provider,
        model_name=original_run.model_name,
        raw_output=new_output,
    )


# =============================================================================
# TSK-073: Evaluation cases + runs + comparison
# =============================================================================

class EvalVerdict(str, Enum):
    PASS    = "pass"
    FAIL    = "fail"
    SKIP    = "skip"


@dataclass
class RubricCriterion:
    """One scoring criterion in an evaluation rubric."""
    name: str
    description: str
    weight: float = 1.0           # relative weight for final score
    max_score: float = 1.0


@dataclass
class EvaluationCase:
    """
    Defines expected behavior for a prompt against a specific input.
    Acceptance (TSK-073): per-case pass/fail; rubric scores.
    """
    case_id: str
    asset_id: str
    description: str
    variable_values: dict[str, str]        # inputs for this case
    expected_contains: list[str] = field(default_factory=list)   # substrings that must appear
    expected_not_contains: list[str] = field(default_factory=list)
    rubric: list[RubricCriterion] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CaseResult:
    """Result for one EvaluationCase against one PromptRun output."""
    case_id: str
    verdict: EvalVerdict
    rubric_scores: dict[str, float]      # criterion_name → score (0.0–max_score)
    overall_score: float                  # weighted average
    failures: list[str]                   # human-readable failure reasons
    run_id: str


@dataclass
class EvaluationRun:
    """
    One evaluation run: scores multiple PromptRuns against their EvaluationCases.
    TSK-073 acceptance: side-by-side comparison on same dataset.
    """
    eval_run_id: str
    asset_id: str
    case_results: list[CaseResult]
    created_at: float = field(default_factory=time.monotonic)

    @property
    def pass_count(self) -> int:
        return sum(1 for r in self.case_results if r.verdict == EvalVerdict.PASS)

    @property
    def fail_count(self) -> int:
        return sum(1 for r in self.case_results if r.verdict == EvalVerdict.FAIL)

    @property
    def pass_rate(self) -> float:
        total = len(self.case_results)
        return self.pass_count / total if total else 0.0

    @property
    def average_score(self) -> float:
        scores = [r.overall_score for r in self.case_results]
        return sum(scores) / len(scores) if scores else 0.0


def evaluate_output(
    case: EvaluationCase,
    output: str,
    run_id: str,
) -> CaseResult:
    """
    Score a model output against an EvaluationCase.
    Returns CaseResult with per-criterion rubric scores and pass/fail verdict.
    """
    failures: list[str] = []

    # Check required substrings
    for expected in case.expected_contains:
        if expected.lower() not in output.lower():
            failures.append(f"Missing expected substring: {expected!r}")

    # Check forbidden substrings
    for forbidden in case.expected_not_contains:
        if forbidden.lower() in output.lower():
            failures.append(f"Unexpected substring found: {forbidden!r}")

    # Rubric scoring (heuristic for each criterion)
    rubric_scores: dict[str, float] = {}
    for criterion in case.rubric:
        # Basic heuristic: full score unless there are failures
        score = criterion.max_score if not failures else 0.0
        rubric_scores[criterion.name] = score

    # Weighted average
    if case.rubric:
        total_weight = sum(c.weight for c in case.rubric)
        overall = sum(
            rubric_scores[c.name] * c.weight / c.max_score
            for c in case.rubric
        ) / total_weight if total_weight else 0.0
    else:
        overall = 1.0 if not failures else 0.0

    verdict = EvalVerdict.PASS if not failures else EvalVerdict.FAIL

    return CaseResult(
        case_id=case.case_id,
        verdict=verdict,
        rubric_scores=rubric_scores,
        overall_score=round(overall, 4),
        failures=failures,
        run_id=run_id,
    )


def run_evaluation(
    eval_run_id: str,
    cases: list[EvaluationCase],
    outputs: dict[str, str],   # case_id → model output string
    run_ids: dict[str, str],   # case_id → run_id
) -> EvaluationRun:
    """
    Run evaluation across all cases.
    outputs and run_ids must have an entry for each case.
    """
    results: list[CaseResult] = []
    for case in cases:
        output = outputs.get(case.case_id, "")
        run_id = run_ids.get(case.case_id, "unknown")
        results.append(evaluate_output(case, output, run_id))

    return EvaluationRun(
        eval_run_id=eval_run_id,
        asset_id=cases[0].asset_id if cases else "",
        case_results=results,
    )
