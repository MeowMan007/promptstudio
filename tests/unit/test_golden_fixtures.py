from __future__ import annotations

import json
from pathlib import Path

import pytest
from prompt_studio_api.contracts.artifact import Artifact
from prompt_studio_api.contracts.registry import load_type_registry
from prompt_studio_api.validation import ValidationContext, validate_project

ROOT = Path(__file__).resolve().parents[2]
GOLDEN_FIXTURES = sorted((ROOT / "fixtures" / "golden").glob("*.json"))


@pytest.mark.parametrize("fixture_path", GOLDEN_FIXTURES, ids=lambda path: path.stem)
def test_golden_project_fixture_validates_without_blockers(fixture_path: Path) -> None:
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    assert fixture["fixture_schema_version"] == load_type_registry().registry_version
    assert fixture["expected_export"]["files"]
    artifacts = [
        Artifact.model_validate(item).model_dump(mode="json") for item in fixture["artifacts"]
    ]
    report = validate_project(
        ValidationContext(
            project_id=fixture["project"]["id"],
            project_revision=fixture["project"]["current_revision"],
            artifacts=artifacts,
            edges=fixture["edges"],
        )
    )

    assert report.blockers == 0, [issue.model_dump() for issue in report.issues]
    assert {artifact["type"] for artifact in artifacts}.issuperset({"screen", "prompt", "skill"})
