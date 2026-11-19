# Runbook: High Prompt Latency

**Incident type:** Prompt run latency exceeds SLO  
**Severity:** P2 — user experience degraded  
**Alert:** `PromptRunLatencyHigh` (WARNING)

## Symptoms
- `ps.prompt.run.duration_ms` p99 > 10 000 ms
- Users reporting slow responses

## Diagnosis
```bash
# Check recent slow runs
curl http://localhost:8000/admin/prompts/slow-runs?threshold_ms=10000 -H "Authorization: Bearer $ADMIN_TOKEN"
# Check model provider status
curl https://status.openai.com/api/v2/status.json
```

## Mitigation
1. If provider incident: add retry with exponential backoff; display degraded-mode banner.
2. If context too long: check binding assembler — `ps.prompt.tokens.total` for the prompt.
3. If cold start: ensure worker pool is warmed.
4. Apply tool cap reduction to reduce total token usage per run.

## Post-incident
- Add p99 latency budget per prompt template.
- Consider caching binding context assembly results.

*TSK-113 / spec 32.3*
