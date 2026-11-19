from __future__ import annotations

# FastAPI uses Depends markers as parameter defaults by design.
# ruff: noqa: B008
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.artifacts.models import ArtifactRecord
from backend.app.canvas.models import ProjectionRecord
from backend.app.canvas.projections import semantic_fields
from backend.app.graph.models import ArtifactEdge
from prompt_studio_api.artifacts import as_contract
from prompt_studio_api.graph_queries import project_membership
from prompt_studio_api.validation import ValidationContext, ValidationReport, validate_project
from prompt_studio_api.workspaces import db_session, session_user

router = APIRouter(prefix="/api/v1/projects/{project_id}", tags=["validation"])


@router.get("/validate", response_model=ValidationReport)
async def validate_project_endpoint(
    project_id: str,
    user: str = Depends(session_user),
    db: AsyncSession = Depends(db_session),
) -> ValidationReport:
    project = await project_membership(db, project_id, user)
    artifact_records = list(
        await db.scalars(
            select(ArtifactRecord).where(
                ArtifactRecord.project_id == project_id,
                ArtifactRecord.deleted_at.is_(None),
            )
        )
    )
    edges = await db.scalars(select(ArtifactEdge).where(ArtifactEdge.project_id == project_id))
    artifacts_by_id = {record.id: record for record in artifact_records}
    context = ValidationContext(
        project_id=project.id,
        project_revision=project.current_revision,
        artifacts=[as_contract(record).model_dump(mode="json") for record in artifact_records],
        edges=[
            {
                "id": edge.id,
                "project_id": edge.project_id,
                "source_id": edge.source_id,
                "target_id": edge.target_id,
                "edge_type": edge.edge_type,
                "metadata": edge.edge_metadata,
            }
            for edge in edges
        ],
        project_revisions=[project.current_revision],
        export_target_revision=project.current_revision,
        projections=[
            {
                "artifact_id": projection.artifact_id,
                "semantic_fields": semantic_fields(artifacts_by_id[projection.artifact_id]),
                "semantic_hash": projection.semantic_hash,
            }
            for projection in await db.scalars(
                select(ProjectionRecord).where(
                    ProjectionRecord.project_id == project_id,
                    ProjectionRecord.artifact_id.is_not(None),
                )
            )
            if projection.artifact_id in artifacts_by_id
        ],
    )
    return validate_project(context)
