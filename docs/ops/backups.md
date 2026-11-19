# Backups and Restore — Prompt Studio

## Objectives

| Target | Value |
|--------|-------|
| RPO (Recovery Point Objective) | ≤ 1 hour |
| RTO (Recovery Time Objective) | ≤ 4 hours |

> [!IMPORTANT]
> The restore procedure must be **drilled at least once per quarter**. Record the drill date,
> operator, and actual recovery time in `docs/ops/restore-drill-log.md`.

---

## Backup Schedule

### Database (PostgreSQL)

- **Continuous WAL archiving** to object storage.
- **Daily logical backups** via `pg_dump` retained for 30 days.
- Backups encrypted at rest (AES-256) with envelope encryption.

```bash
# Manual on-demand backup
make backup-db        # triggers pg_dump → uploads to backup bucket
```

### Object Storage (Artifacts)

- Cross-region replication enabled for production bucket.
- Versioning enabled — 90-day version retention.

---

## Restore Procedure

### 1. Restore from latest daily backup

```bash
# Download and decrypt the latest backup
make restore-db BACKUP=latest

# Verify row counts
make verify-db-restore
```

### 2. Restore from point-in-time (WAL)

```bash
# Restore to a specific timestamp
make restore-db-pitr TIMESTAMP="2024-01-01T12:00:00Z"
```

### 3. Object storage restore

```bash
# Restore artifact bucket from replication
make restore-bucket REGION=secondary
```

---

## Restore Drill Checklist

- [ ] Identify target restore point
- [ ] Spin up restore environment (do NOT restore to production directly)
- [ ] Run `make restore-db BACKUP=<target>`
- [ ] Run `make verify-db-restore` — confirm row counts match
- [ ] Run `make test` against restored DB
- [ ] Record drill date and RTO in restore-drill-log.md
- [ ] Tear down restore environment

---

*TSK-112 / spec 31*
