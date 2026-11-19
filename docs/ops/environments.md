# Environments — Prompt Studio

## Overview

Prompt Studio runs in three tiers:

| Tier | Purpose | DB | Bucket | Key Source |
|------|---------|-----|--------|------------|
| `local` | Developer workstation | Local Postgres | MinIO | `.env` file (never committed) |
| `staging` | Pre-production QA | Managed Postgres | Cloud bucket | Secrets store |
| `production` | Live product | Managed Postgres | Cloud bucket | Secrets store |

> [!CAUTION]
> **Secrets are never committed to the repository.** The `.env` file is in `.gitignore`.
> All production and staging secrets are injected at deploy time from the secrets store.

---

## Secrets Store

Production and staging secrets are managed via environment variables injected by the
deployment platform (e.g., Railway, Render, Fly.io, GCP Secret Manager).

Required secrets:

| Variable | Purpose |
|---------|---------|
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `S3_ENDPOINT_URL` | Object-storage endpoint |
| `S3_ACCESS_KEY` | Object-storage access key |
| `S3_SECRET_KEY` | Object-storage secret key |
| `S3_BUCKET_NAME` | Primary artifact bucket |
| `MODEL_API_KEY` | LLM provider API key |
| `JWT_SECRET` | JWT signing secret |
| `EXPORT_SCAN_ENABLED` | `true` to enable secret scanning |

---

## Environment Parity

- Staging DB and bucket are **separate from production** — never shared.
- Schema migrations are applied to staging first, then production.
- Staging is kept within 24 hours of production data (anonymised snapshot).

---

## Deployment

```bash
# Deploy to staging
make deploy-staging

# Deploy to production (requires 2-person review)
make deploy-production
```

Both targets run `make test` and `make export-check` as a pre-flight gate.

---

*TSK-111 / spec 32.1*
