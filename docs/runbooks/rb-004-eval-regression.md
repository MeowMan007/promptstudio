# Runbook: Prompt Eval Regression Detected

**Incident type:** Prompt regression gate failed in CI  
**Severity:** P1 — version promotion blocked  
**Alert:** `PromptEvalRegressionGateFailed` CI check

## Symptoms
- CI pipeline fails on `make eval`
- `RegressionError` in eval log with delta below threshold

## Diagnosis
```bash
# Run eval locally against incumbent and candidate
make eval PROMPT_ID=<id> VERSION=<candidate> INCUMBENT=<incumbent>
# Review per-case assertion results
cat evals/results/<run_id>.json | python -m json.tool
```

## Mitigation
1. Review which assertion types failed (deterministic vs rubric).
2. If regression is in rubric only: may be acceptable — escalate to prompt owner.
3. If regression is in deterministic assertions: the prompt change broke known behaviour.
   - Revert the prompt change, OR
   - Update the eval dataset to reflect intentionally changed behaviour (requires review).
4. Never delete a failing eval case — fix the prompt or document the deliberate change.

## Post-incident
- Add a regression test case for the failure mode.

*TSK-113 / spec 32.3*
