from __future__ import annotations

# FastAPI uses Depends markers as parameter defaults by design.
# ruff: noqa: B008
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.artifacts.models import ArtifactRecord, ArtifactRevisionRecord
from backend.app.graph.edges import creates_cycle
from backend.app.graph.models import ArtifactEdge
from backend.app.ids import allocate_artifact_identity, new_ulid
from backend.app.projects.models import Project, ProjectEvent
from prompt_studio_api.artifacts import (
    as_contract,
    check_base_revision,
    project_for_write,
    record_artifact_change,
    validate_contract,
)
from prompt_studio_api.contracts.artifact import (
    ArtifactStatus,
    Provenance,
    ProvenanceOrigin,
    Sensitivity,
)
from prompt_studio_api.contracts.registry import EdgeDefinition, validate_edge_pair
from prompt_studio_api.workspaces import (
    audit,
    correlation_id,
    db_session,
    membership,
    require_role,
    session_user,
)

router = APIRouter(prefix="/api/v1", tags=["graph"])


class EdgeCreate(BaseModel):
    base_revision: int = Field(ge=0)
    source_id: str
    target_id: str
    edge_type: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    reason: str = Field(min_length=5, max_length=1000)


class EdgeOut(BaseModel):
    id: str
    project_id: str
    source_id: str
    target_id: str
    edge_type: str
    metadata: dict[str, Any]
    created_by: str
    created_at: datetime


class EdgeCreated(EdgeOut):
    created_issue_id: str | None = None


async def edge_endpoints(
    db: AsyncSession, project_id: str, source_id: str, target_id: str
) -> tuple[ArtifactRecord, ArtifactRecord]:
    records = list(
        await db.scalars(
            select(ArtifactRecord).where(
                ArtifactRecord.project_id == project_id,
                ArtifactRecord.id.in_([source_id, target_id]),
                ArtifactRecord.deleted_at.is_(None),
            )
        )
    )
    by_id = {record.id: record for record in records}
    source = by_id.get(source_id)
    target = by_id.get(target_id)
    if source is None or target is None:
        raise HTTPException(status_code=404, detail="Edge endpoint not found in this project")
    if source_id == target_id:
        raise HTTPException(status_code=422, detail="An artifact cannot be linked to itself")
    return source, target


def pair_definition(edge_type: str, source_type: str, target_type: str) -> EdgeDefinition:
    try:
        return validate_edge_pair(edge_type, source_type, target_type)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "graph.invalid_edge",
                "message": str(exc),
                "details": {
                    "edge_type": edge_type,
                    "source_type": source_type,
                    "target_type": target_type,
                },
            },
        ) from exc


async def record_edge_event(
    db: AsyncSession,
    request: Request,
    project: Project,
    actor: str,
    edge_id: str,
    event_type: str,
    reason: str,
) -> None:
    project.current_revision += 1
    db.add(
        ProjectEvent(
            id=new_ulid(),
            project_id=project.id,
            revision=project.current_revision,
            event_type=event_type,
            payload={"edge_id": edge_id},
            actor_id=actor,
            correlation_id=correlation_id(request),
        )
    )
    audit(db, request, actor, project.workspace_id, event_type, "edge", edge_id, reason)


async def create_contradiction_issue(
    db: AsyncSession,
    request: Request,
    project: Project,
    source: ArtifactRecord,
    target: ArtifactRecord,
    actor: str,
    reason: str,
) -> ArtifactRecord:
    owner = source.owner or actor
    payload: dict[str, Any] = {
        "statement": f"{source.alias} contradicts {target.alias}",
        "severity": "medium",
        "owner": owner,
    }
    issue_id, alias = await allocate_artifact_identity(
        db, project_id=project.id, artifact_type="issue"
    )
    now = datetime.now(UTC)
    issue = ArtifactRecord(
        id=issue_id,
        project_id=project.id,
        alias=alias,
        type="issue",
        schema_version="1.0.0",
        title=f"Contradiction: {source.alias} / {target.alias}",
        body="",
        payload=payload,
        status=ArtifactStatus.SCRATCH.value,
        revision=1,
        created_by=actor,
        updated_by=actor,
        provenance=Provenance(origin=ProvenanceOrigin.SYSTEM).model_dump(mode="json"),
        visibility="project",
        sensitivity=Sensitivity.INTERNAL.value,
        locked_fields=[],
        owner=owner,
        tags=[],
        created_at=now,
        updated_at=now,
    )
    validate_contract(issue)
    db.add(issue)
    await db.flush()
    contract = as_contract(issue)
    db.add(
        ArtifactRevisionRecord(
            id=new_ulid(),
            artifact_id=issue.id,
            revision=1,
            snapshot=contract.model_dump(mode="json"),
            change_summary=reason,
            actor_id=actor,
        )
    )
    project.current_revision += 1
    db.add(
        ProjectEvent(
            id=new_ulid(),
            project_id=project.id,
            revision=project.current_revision,
            event_type="artifact.created",
            payload={"artifact_id": issue.id, "artifact_revision": 1},
            actor_id=actor,
            correlation_id=correlation_id(request),
        )
    )
    audit(
        db, request, actor, project.workspace_id, "artifact.created", "artifact", issue.id, reason
    )
    return issue


@router.post("/projects/{project_id}/edges", response_model=EdgeCreated, status_code=201)
async def create_edge(
    project_id: str,
    payload: EdgeCreate,
    request: Request,
    user: str = Depends(session_user),
    db: AsyncSession = Depends(db_session),
) -> EdgeCreated:
    project = await project_for_write(db, project_id)
    member = await membership(db, project.workspace_id, user)
    require_role(member, "owner", "editor")
    check_base_revision(payload.base_revision, project.current_revision)
    source, target = await edge_endpoints(db, project_id, payload.source_id, payload.target_id)
    definition = pair_definition(payload.edge_type, source.type, target.type)
    edge_metadata = dict(payload.metadata)
    existing_edge = await db.scalar(
        select(ArtifactEdge.id).where(
            ArtifactEdge.project_id == project_id,
            ArtifactEdge.source_id == source.id,
            ArtifactEdge.target_id == target.id,
            ArtifactEdge.edge_type == payload.edge_type,
        )
    )
    if existing_edge is not None:
        raise HTTPException(status_code=409, detail="Edge already exists")

    if payload.edge_type == "contains":
        existing_parent = await db.scalar(
            select(ArtifactEdge.id).where(
                ArtifactEdge.project_id == project_id,
                ArtifactEdge.target_id == target.id,
                ArtifactEdge.edge_type == "contains",
            )
        )
        if existing_parent is not None:
            raise HTTPException(status_code=409, detail="Contained artifact already has a parent")

    if definition.acyclic:
        existing = list(
            await db.execute(
                select(ArtifactEdge.source_id, ArtifactEdge.target_id).where(
                    ArtifactEdge.project_id == project_id,
                    ArtifactEdge.edge_type == payload.edge_type,
                )
            )
        )
        if creates_cycle(
            existing,
            source_id=payload.source_id,
            target_id=payload.target_id,
        ):
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "conflict.graph_cycle",
                    "message": f"{payload.edge_type} edges cannot contain a cycle",
                    "details": {"edge_type": payload.edge_type},
                },
            )

    if payload.edge_type == "blocks" and not source.owner:
        raise HTTPException(status_code=422, detail="The blocking artifact must have an owner")
    if payload.edge_type == "supersedes":
        if target.status != "approved":
            raise HTTPException(
                status_code=409, detail="Only an approved artifact can be superseded"
            )
        edge_metadata["reason"] = payload.reason
        edge_metadata["_superseded_previous_status"] = target.status

    edge = ArtifactEdge(
        id=new_ulid(),
        project_id=project_id,
        source_id=source.id,
        target_id=target.id,
        edge_type=payload.edge_type,
        edge_metadata=edge_metadata,
        created_by=user,
    )
    db.add(edge)
    await db.flush()

    if payload.edge_type == "supersedes":
        target.status = "deprecated"
        await record_artifact_change(
            db,
            request,
            target,
            project,
            user,
            event_type="artifact.updated",
            reason=payload.reason,
        )

    issue = None
    if payload.edge_type == "contradicts":
        issue = await create_contradiction_issue(
            db, request, project, source, target, user, payload.reason
        )

    await record_edge_event(db, request, project, user, edge.id, "edge.created", payload.reason)
    await db.commit()
    await db.refresh(edge)
    return EdgeCreated(
        id=edge.id,
        project_id=edge.project_id,
        source_id=edge.source_id,
        target_id=edge.target_id,
        edge_type=edge.edge_type,
        metadata=edge.edge_metadata,
        created_by=edge.created_by,
        created_at=edge.created_at,
        created_issue_id=issue.id if issue is not None else None,
    )


@router.get("/projects/{project_id}/edges", response_model=list[EdgeOut])
async def list_edges(
    project_id: str,
    user: str = Depends(session_user),
    db: AsyncSession = Depends(db_session),
) -> list[EdgeOut]:
    project = await db.get(Project, project_id)
    if project is None or project.status != "active":
        raise HTTPException(status_code=404, detail="Project not found")
    await membership(db, project.workspace_id, user)
    result = await db.scalars(
        select(ArtifactEdge)
        .where(ArtifactEdge.project_id == project_id)
        .order_by(ArtifactEdge.created_at, ArtifactEdge.id)
    )
    return [
        EdgeOut(
            id=edge.id,
            project_id=edge.project_id,
            source_id=edge.source_id,
            target_id=edge.target_id,
            edge_type=edge.edge_type,
            metadata=edge.edge_metadata,
            created_by=edge.created_by,
            created_at=edge.created_at,
        )
        for edge in result
    ]


@router.delete("/projects/{project_id}/edges/{edge_id}", status_code=204)
async def delete_edge(
    project_id: str,
    edge_id: str,
    request: Request,
    base_revision: int = Query(ge=0),
    reason: str = Query(min_length=5, max_length=1000),
    user: str = Depends(session_user),
    db: AsyncSession = Depends(db_session),
) -> None:
    project = await project_for_write(db, project_id)
    member = await membership(db, project.workspace_id, user)
    require_role(member, "owner", "editor")
    check_base_revision(base_revision, project.current_revision)
    edge = await db.scalar(
        select(ArtifactEdge).where(
            ArtifactEdge.id == edge_id, ArtifactEdge.project_id == project_id
        )
    )
    if edge is None:
        raise HTTPException(status_code=404, detail="Edge not found")
    if edge.edge_type == "supersedes":
        target = await db.get(ArtifactRecord, edge.target_id)
        previous_status = edge.edge_metadata.get("_superseded_previous_status")
        if target is not None and isinstance(previous_status, str):
            target.status = previous_status
            await record_artifact_change(
                db,
                request,
                target,
                project,
                user,
                event_type="artifact.updated",
                reason=reason,
            )
    await db.delete(edge)
    await record_edge_event(db, request, project, user, edge.id, "edge.deleted", reason)
    await db.commit()
