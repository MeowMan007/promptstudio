from __future__ import annotations

import hashlib
import json
from typing import Any

from backend.app.artifacts.models import ArtifactRecord


def semantic_fields(artifact: ArtifactRecord) -> dict[str, Any]:
    return {
        "alias": artifact.alias,
        "body": artifact.body,
        "owner": artifact.owner,
        "payload": artifact.payload,
        "provenance": artifact.provenance,
        "schema_version": artifact.schema_version,
        "sensitivity": artifact.sensitivity,
        "status": artifact.status,
        "tags": artifact.tags,
        "title": artifact.title,
        "type": artifact.type,
        "visibility": artifact.visibility,
    }


def semantic_hash_for_artifact(artifact: ArtifactRecord) -> str:
    serialized = json.dumps(
        semantic_fields(artifact),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(serialized).hexdigest()}"
