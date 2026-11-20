# Deploying Prompt Studio

## Quick Deploy Options

### Option 1 — Railway (recommended, free tier)

1. Go to [railway.app](https://railway.app) and sign in with GitHub
2. Click **New Project → Deploy from GitHub repo** → select `MeowMan007/promptstudio`
3. Railway auto-detects the `Dockerfile` and `railway.toml`
4. Add these environment variables in Railway dashboard:
   - `APP_ENV` = `production`
   - `SESSION_SECRET_KEY` = *(generate a 48-char random string)*
   - `DATABASE_URL` = *(add a Railway Postgres plugin — it auto-injects this)*
5. Click **Deploy** — your URL will be `https://promptstudio-production.up.railway.app`

> **Canvas works without a database.** You only need `DATABASE_URL` if you want persistent workspaces/artifacts.

---

### Option 2 — Render (free tier, cold starts)

1. Go to [render.com](https://render.com) → **New → Blueprint**
2. Connect `MeowMan007/promptstudio` — Render reads `render.yaml` automatically
3. It creates a **web service** (Docker) + a **Postgres** database in one click
4. Set `SESSION_SECRET_KEY` as a secret env var in Render dashboard
5. Your URL will be `https://prompt-studio.onrender.com`

---

### Option 3 — Fly.io (global edge, free allowance)

```bash
fly launch --dockerfile Dockerfile --name prompt-studio --region sin
fly secrets set SESSION_SECRET_KEY=$(openssl rand -base64 48)
fly secrets set APP_ENV=production
fly deploy
```

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `PORT` | No | `8000` | Injected automatically by Railway / Render |
| `APP_ENV` | Yes in prod | `development` | Set to `production` |
| `SESSION_SECRET_KEY` | Yes in prod | *(auto-gen in dev)* | ≥ 32-char random string |
| `DATABASE_URL` | No | *(in-memory mode)* | PostgreSQL connection URL |
| `OIDC_ISSUER` | No | — | For Google/Auth0 login |
| `OIDC_CLIENT_ID` | No | — | For Google/Auth0 login |
| `OIDC_CLIENT_SECRET` | No | — | For Google/Auth0 login |

## Health Check

`GET /health` → `{"status": "ok"}` — used by Railway / Render to confirm startup.
