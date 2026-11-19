"""Create ignored local-only credentials used by the development containers."""

from __future__ import annotations

import secrets
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parents[1] / ".env"


def main() -> None:
    existing_lines = ENV_PATH.read_text(encoding="utf-8").splitlines() if ENV_PATH.exists() else []
    values = {
        line.partition("=")[0]: line.partition("=")[2] for line in existing_lines if "=" in line
    }
    defaults = {
        "POSTGRES_PASSWORD": secrets.token_urlsafe(32),
        "MINIO_ROOT_USER": "promptstudio-local",
        "MINIO_ROOT_PASSWORD": secrets.token_urlsafe(32),
        "SESSION_SECRET_KEY": secrets.token_urlsafe(48),
        "APP_ENV": "development",
        "SESSION_TTL_SECONDS": "3600",
        "SESSION_COOKIE_SECURE": "false",
        "REDIS_URL": "redis://127.0.0.1:6379/0",
        "S3_ENDPOINT_URL": "http://127.0.0.1:9000",
    }
    for key, value in defaults.items():
        if not values.get(key):
            values[key] = value
    if not values.get("DATABASE_URL"):
        values["DATABASE_URL"] = (
            "postgresql+asyncpg://prompt_studio:"
            f"{values['POSTGRES_PASSWORD']}@127.0.0.1:5432/prompt_studio"
        )

    updated_lines: list[str] = []
    written_keys: set[str] = set()
    for line in existing_lines:
        if "=" not in line:
            updated_lines.append(line)
            continue
        key = line.partition("=")[0]
        if key in values and key not in written_keys:
            updated_lines.append(f"{key}={values[key]}")
            written_keys.add(key)
        else:
            updated_lines.append(line)
    updated_lines.extend(
        f"{key}={value}" for key, value in values.items() if key not in written_keys
    )
    ENV_PATH.write_text("\n".join([*updated_lines, ""]), encoding="utf-8")
    ENV_PATH.chmod(0o600)


if __name__ == "__main__":
    main()
