# ── Stage 1: build ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Copy dependency files
COPY pyproject.toml uv.lock ./
COPY apps/api/pyproject.toml apps/api/

# Install Python dependencies into /app/.venv (all workspace packages, no dev extras)
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
RUN uv sync --frozen --all-packages --no-dev

# ── Stage 2: runtime ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Copy venv from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application source
COPY apps/api/src ./apps/api/src
COPY backend ./backend
COPY schemas ./schemas
COPY packages ./packages

# Make the venv's python the default
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/apps/api/src:/app"

# Railway / Render inject PORT at runtime; default to 8000
ENV PORT=8000
ENV APP_ENV=production

EXPOSE $PORT

CMD uvicorn prompt_studio_api.main:app \
      --host 0.0.0.0 \
      --port ${PORT} \
      --workers 2 \
      --proxy-headers \
      --forwarded-allow-ips="*"
