# Runbook: Kill Switch Activated

**Incident type:** Agency kill switch triggered  
**Severity:** P0 — all tool calls halted  
**Alert:** `KillSwitchActivated` (CRITICAL)

## Symptoms
- `ps.agency.kill_switch.total` counter > 0
- All tool calls returning `KillSwitchError`
- Orchestrator stuck in HUMAN_REVIEW state

## Diagnosis
```bash
# Check router state via admin API
curl -H "Authorization: Bearer $ADMIN_TOKEN" http://localhost:8000/admin/router/status
```

## Mitigation
1. Identify reason from `kill_switch_reason` field in router status.
2. If false positive: reset kill switch via admin API:
   ```bash
   curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" http://localhost:8000/admin/router/reset-kill-switch
   ```
3. If legitimate (cost overrun, injection detected): do NOT reset until root cause resolved.
4. Review `ps.agency.*` metrics in dashboard for cost/call data.

## Post-incident
- Raise cost caps or rate limits if needed.
- Review prompt templates for injection vulnerabilities.

*TSK-113 / spec 32.3*
