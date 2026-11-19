from __future__ import annotations

import subprocess


def test_local_development_services_are_healthy() -> None:
    container_ids = subprocess.run(
        ["docker", "compose", "ps", "-q", "postgres", "redis", "minio", "mail"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    assert len(container_ids) == 4

    health = subprocess.run(
        ["docker", "inspect", "--format={{.State.Health.Status}}", *container_ids],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    assert health == ["healthy"] * 4
