# Runbook: Secret Detected in Export

**Incident type:** Secret scanner flagged content in export package  
**Severity:** P0 — potential data leak  
**Alert:** `SecretDetectedInExport` (CRITICAL)

## Symptoms
- `ps.export.secrets_detected.total` > 0
- Export job blocked / redacted content in package

## Diagnosis
```bash
# Check export job scan report
curl -H "Authorization: Bearer $ADMIN_TOKEN" http://localhost:8000/exports/{job_id}/scan-report
```

## Mitigation
1. Do NOT deliver the export package to the user until cleared.
2. Review `scan_report.findings` to identify which file and pattern triggered.
3. If false positive (e.g., test data): add pattern to allowlist in `pipeline.py`.
4. If real secret: notify security team; rotate the exposed credential immediately.
5. Re-run export with the content remediated.

## Post-incident
- Identify how secret entered the project (direct paste, skill import, binding?).
- Tighten validation at the entry point.

*TSK-113 / spec 32.3*
