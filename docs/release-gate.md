# Release Gate Checklist — Prompt Studio v1.0

> This checklist must be completed and signed off by two engineers before tagging `v1.0`.
> All items must be ✅ PASS or explicitly waived with a written justification.

## EX (Export) Gate Criteria

| # | Criterion | Status | Notes |
|---|-----------|--------|-------|
| EX-01 | All export generators produce valid output | ☐ | Run `make export-check` |
| EX-02 | Round-trip: export → import → export checksums match | ☐ | Run `make test-roundtrip` |
| EX-03 | Secret scanner catches all hostile-fixture payloads | ☐ | Run `make security` |
| EX-04 | OpenAPI validates against OAS 3.1 | ☐ | Run `make export-check` |
| EX-05 | DDL/DBML parity test passes | ☐ | Run `make export-check` |
| EX-06 | All Mermaid diagrams parse | ☐ | Run `make export-check` |
| EX-07 | llms.txt generated and valid | ☐ | Run `make export-check` |
| EX-08 | AGENTS.md deterministic (same hash on re-run) | ☐ | Run `make export-check` |

## Security Gate Criteria

| # | Criterion | Status | Notes |
|---|-----------|--------|-------|
| SEC-01 | All path-traversal payloads blocked | ☐ | Run `make security` |
| SEC-02 | All secret payloads detected | ☐ | Run `make security` |
| SEC-03 | Tenant isolation verified (IDOR tests) | ☐ | Run `make security` |
| SEC-04 | Kill switch tested | ☐ | Run `make security` |
| SEC-05 | Agency budget caps verified | ☐ | Run `make security` |
| SEC-06 | Red-team corpus: zero successful violations | ☐ | Run `make security` |

## Test Suite Gate

| # | Criterion | Status | Notes |
|---|-----------|--------|-------|
| TEST-01 | All unit tests pass: `make test` | ☐ | Zero failures |
| TEST-02 | Contract tests pass: `make test-contract` | ☐ | Zero failures |
| TEST-03 | Prompt regression gate passes: `make eval` | ☐ | All prompts green |
| TEST-04 | No tests marked `xfail` without written reason | ☐ | Manual review |

## Operational Readiness

| # | Criterion | Status | Notes |
|---|-----------|--------|-------|
| OPS-01 | Staging environment verified | ☐ | `docs/ops/environments.md` |
| OPS-02 | Backup restore drill completed | ☐ | `docs/ops/backups.md` |
| OPS-03 | All 5 runbooks written and rehearsed | ☐ | `docs/runbooks/` |
| OPS-04 | Dashboards and alert rules deployed | ☐ | Grafana/Cloud Monitoring |
| OPS-05 | On-call rotation defined | ☐ | PagerDuty / equivalent |

## Documentation

| # | Criterion | Status | Notes |
|---|-----------|--------|-------|
| DOC-01 | User guide complete | ☐ | `docs/user-guide.md` |
| DOC-02 | Agent guide complete | ☐ | `docs/agent-guide.md` |
| DOC-03 | ADR index: ADR-001 through ADR-008 | ☐ | `docs/adr/INDEX.md` |
| DOC-04 | CHANGELOG.md current | ☐ | Covers all EPIC-01..12 |

## Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Engineering Lead | | | |
| Security Reviewer | | | |

---

## Tag Procedure

Once all items are ✅:

```bash
git tag -a v1.0.0 -m "Prompt Studio v1.0 release"
git push origin v1.0.0
```

---

*TSK-118 / spec 27 + 33*
