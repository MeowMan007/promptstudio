# Prompt Studio

A prompt-native visual workspace for designing applications. The canvas is a projection of a typed project graph; field-scoped prompts, installable skills, and deterministic project exports support a reviewable AI-assisted workflow.

## Status

Implementation follows `MASTER_PLAN.yaml`; task statuses are updated only after their verification
commands pass. The API foundation now includes OIDC sessions, tenant-isolated workspaces, projects,
typed artifacts, revisions, edges and graph queries.

## Prerequisites

- Node.js and pnpm (see `package.json` for the pinned package manager)
- Python 3.12+ and uv
- GNU Make for the documented `make` commands

## Setup

```sh
make setup
```

See `AGENTS.md` for repository conventions and `MASTER_PLAN.yaml` for task acceptance criteria.

## Contracts

Pydantic models in `apps/api` generate JSON Schemas in `schemas/`; the TypeScript contracts in
`packages/contracts/src/generated/` are generated from those schemas. Run `make generate-contracts`
after changing a model, and `make test-contract` to detect drift.

Run the API locally with `make api` after `make setup`.

## API surface

The API exposes workspace and project CRUD under `/api/v1`, artifact CRUD and revision history at
`/api/v1/projects/{project_id}/artifacts` and `/api/v1/artifacts/{artifact_id}`, and typed graph
edges under `/api/v1/projects/{project_id}/edges`. Graph reads include depth-limited neighbourhood,
impact and requirement traceability queries under `/api/v1/projects/{project_id}/graph`.

Artifact types and edge directions come from the versioned JSON registries in `machine/`. Payload
schemas for version `1.0.0` are generated from the type registry and validated before persistence.
Artifact writes require a base revision and reason; IDs and per-project aliases are assigned by the
server inside the create transaction. Archiving keeps revision history and supports restoration.

## Authentication

The API uses the configured managed OpenID Connect issuer. Set `OIDC_ISSUER`, `OIDC_CLIENT_ID`,
`OIDC_CLIENT_SECRET`, and the provider's callback URL (`OIDC_REDIRECT_URI`, ending in
`/auth/callback`) in the ignored local `.env` file. The session cookie contains only the provider
subject and expiry; it is HttpOnly, SameSite=Lax, and Secure in production. Unconfigured login
returns HTTP 503. `SESSION_TTL_SECONDS` defaults to one hour.
