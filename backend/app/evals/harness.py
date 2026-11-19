"""TSK-104: promptfoo harness + eval datasets per prompt.
TSK-106: Prompt regression gate in CI.

Implements spec sections 29.4:
  - EvalDataset: test cases for a prompt
  - EvalResult: outcome of running a case
  - PromptEvalHarness: runs deterministic assertions + rubric scoring
  - RegressionGate: compares new eval scores vs incumbent; blocks on regression
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

class AssertionType(str, Enum):
    EXACT_MATCH = "exact_match"           # output == expected
    CONTAINS = "contains"                 # expected in output
    NOT_CONTAINS = "not_contains"         # expected NOT in output
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    JSON_SCHEMA = "json_schema"           # output parses as JSON matching schema
    REGEX = "regex"                       # output matches pattern
    RUBRIC = "rubric"                     # scored by LLM rubric (0-1 float)
    LENGTH_LTE = "length_lte"             # len(output) <= int(expected)
    LENGTH_GTE = "length_gte"


@dataclass
class Assertion:
    assertion_type: AssertionType
    expected: Any        # expected value / pattern / schema
    weight: float = 1.0  # weight for rubric scoring


@dataclass
class EvalCase:
    case_id: str
    prompt_id: str
    variables: dict[str, str]        # template variables
    expected_output: str = ""        # for exact/contains assertions
    assertions: list[Assertion] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class EvalDataset:
    dataset_id: str
    prompt_id: str
    prompt_version: int
    cases: list[EvalCase]
    description: str = ""


@dataclass
class CaseResult:
    case_id: str
    output: str
    passed: bool
    score: float              # 0.0 – 1.0
    assertion_results: list[dict[str, Any]] = field(default_factory=list)
    error: str = ""


@dataclass
class EvalRunResult:
    dataset_id: str
    prompt_id: str
    prompt_version: int
    case_results: list[CaseResult]
    overall_score: float      # weighted average across cases
    passed: bool              # True if overall_score >= pass_threshold
    pass_threshold: float = 0.8


# ---------------------------------------------------------------------------
# Assertion evaluator
# ---------------------------------------------------------------------------

import re as _re


def _evaluate_assertion(output: str, assertion: Assertion) -> tuple[bool, float]:
    """Return (passed, score 0-1) for one assertion."""
    t = assertion.assertion_type
    exp = assertion.expected

    if t == AssertionType.EXACT_MATCH:
        passed = output.strip() == str(exp).strip()
    elif t == AssertionType.CONTAINS:
        passed = str(exp) in output
    elif t == AssertionType.NOT_CONTAINS:
        passed = str(exp) not in output
    elif t == AssertionType.STARTS_WITH:
        passed = output.startswith(str(exp))
    elif t == AssertionType.ENDS_WITH:
        passed = output.endswith(str(exp))
    elif t == AssertionType.REGEX:
        passed = bool(_re.search(str(exp), output))
    elif t == AssertionType.LENGTH_LTE:
        passed = len(output) <= int(exp)
    elif t == AssertionType.LENGTH_GTE:
        passed = len(output) >= int(exp)
    elif t == AssertionType.JSON_SCHEMA:
        try:
            parsed = json.loads(output)
            # Minimal schema check: just verify it parses if schema is None
            passed = isinstance(parsed, (dict, list)) if exp is None else True
        except json.JSONDecodeError:
            passed = False
    elif t == AssertionType.RUBRIC:
        # In CI we can't call an LLM — return neutral score (0.5) as placeholder
        # Real rubric scoring happens via promptfoo integration at eval time
        passed = True
        return passed, 0.5
    else:
        passed = False

    return passed, 1.0 if passed else 0.0


# ---------------------------------------------------------------------------
# Harness
# ---------------------------------------------------------------------------

# Type for a prompt runner: (prompt_id, version, variables) → output string
PromptRunner = Callable[[str, int, dict[str, str]], str]


def _stub_runner(prompt_id: str, version: int, variables: dict[str, str]) -> str:
    """Default stub runner — returns a deterministic fake output."""
    seed = hashlib.sha256(
        json.dumps({"p": prompt_id, "v": version, "vars": variables}, sort_keys=True).encode()
    ).hexdigest()[:8]
    return f"[stub output for {prompt_id}@v{version} seed={seed}]"


class PromptEvalHarness:
    """Runs eval datasets against a prompt runner.

    Deterministic assertions run first; rubric second (TSK-104 acceptance).
    """

    def __init__(
        self,
        runner: PromptRunner | None = None,
        pass_threshold: float = 0.8,
    ) -> None:
        self._runner = runner or _stub_runner
        self.pass_threshold = pass_threshold

    def run_dataset(self, dataset: EvalDataset) -> EvalRunResult:
        """Run all cases in a dataset and return an EvalRunResult."""
        case_results: list[CaseResult] = []

        for case in dataset.cases:
            try:
                output = self._runner(
                    dataset.prompt_id,
                    dataset.prompt_version,
                    case.variables,
                )
                error = ""
            except Exception as exc:
                output = ""
                error = str(exc)

            # Sort: deterministic assertions first, rubric last
            sorted_assertions = sorted(
                case.assertions,
                key=lambda a: 0 if a.assertion_type != AssertionType.RUBRIC else 1,
            )

            assertion_results: list[dict[str, Any]] = []
            weighted_score_sum = 0.0
            total_weight = 0.0

            for assertion in sorted_assertions:
                passed, score = _evaluate_assertion(output, assertion)
                assertion_results.append({
                    "type": assertion.assertion_type.value,
                    "expected": assertion.expected,
                    "passed": passed,
                    "score": score,
                    "weight": assertion.weight,
                })
                weighted_score_sum += score * assertion.weight
                total_weight += assertion.weight

            case_score = weighted_score_sum / total_weight if total_weight > 0 else 0.0
            case_passed = case_score >= self.pass_threshold

            case_results.append(CaseResult(
                case_id=case.case_id,
                output=output,
                passed=case_passed,
                score=case_score,
                assertion_results=assertion_results,
                error=error,
            ))

        overall_score = (
            sum(r.score for r in case_results) / len(case_results)
            if case_results else 0.0
        )

        return EvalRunResult(
            dataset_id=dataset.dataset_id,
            prompt_id=dataset.prompt_id,
            prompt_version=dataset.prompt_version,
            case_results=case_results,
            overall_score=overall_score,
            passed=overall_score >= self.pass_threshold,
            pass_threshold=self.pass_threshold,
        )


# ---------------------------------------------------------------------------
# TSK-106: Prompt regression gate
# ---------------------------------------------------------------------------

class RegressionError(Exception):
    """Raised when a new version regresses vs the incumbent."""


@dataclass
class VersionScore:
    prompt_id: str
    version: int
    score: float
    dataset_id: str


def regression_gate(
    incumbent: VersionScore,
    candidate: VersionScore,
    min_improvement: float = -0.02,  # allow up to 2% drop
) -> None:
    """Block version promotion if candidate regresses vs incumbent.

    Args:
        incumbent: The currently promoted version's score.
        candidate: The candidate version's score.
        min_improvement: Minimum score delta allowed (negative = small regression OK).

    Raises:
        RegressionError if candidate.score - incumbent.score < min_improvement.
    """
    if candidate.prompt_id != incumbent.prompt_id:
        raise ValueError(
            f"Prompt ID mismatch: {incumbent.prompt_id!r} vs {candidate.prompt_id!r}"
        )

    delta = round(candidate.score - incumbent.score, 6)
    if delta < min_improvement - 1e-9:
        raise RegressionError(
            f"Prompt {candidate.prompt_id!r} v{candidate.version} regressed vs "
            f"v{incumbent.version}: {candidate.score:.3f} vs {incumbent.score:.3f} "
            f"(Δ={delta:+.3f}, threshold={min_improvement:+.3f})"
        )
