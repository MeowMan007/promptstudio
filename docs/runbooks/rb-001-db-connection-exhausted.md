# Runbook: DB Connection Exhausted

**Incident type:** PostgreSQL max_connections reached  
**Severity:** P1 — service degraded  
**Alert:** `PromptRunErrorRateHigh` + `pg_stat_activity` saturation

## Symptoms
- 500 errors from API with `too many connections` in logs
- `ps.prompt.run.total{status=error}` spiking

## Diagnosis
```bash
# Check active connections
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity WHERE state != 'idle';"
# Check pool stats
curl http://localhost:8000/health | jq .db_pool
```

## Mitigation
1. Identify long-running idle connections: `SELECT pid, query, state, now() - query_start FROM pg_stat_activity WHERE state = 'idle' ORDER BY query_start;`
2. Terminate idle connections: `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND now() - query_start > interval '5 minutes';`
3. If pool misconfigured, update `DB_POOL_SIZE` env var and redeploy.

## Post-incident
- Add connection pooler (PgBouncer) if recurring.
- File ADR if architectural change needed.

*TSK-113 / spec 32.3*
