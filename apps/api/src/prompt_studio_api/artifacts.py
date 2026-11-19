from __future__ import annotations

# FastAPI uses Depends markers as parameter defaults by design.
# ruff: noqa: B008
from datetime import UTC, datetime
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import func, or_, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.artifacts.models import ArtifactRecord, ArtifactRevisionRecord
from backend.app.identity.models import WorkspaceMember
from backend.app.ids import allocate_artifact_identity, new_ulid
from backend.app.projects.models import Project, ProjectEvent
from prompt_studio_api.contracts.artifact import (
    Artifact,
    ArtifactStatus,
    Provenance,
    ProvenanceOrigin,
    Sensitivity,
)
from prompt_studio_api.workspaces import (
    audit,
    correlation_id,
    db_session,
    membership,
    require_role,
    session_user,
)

router = APIRouter(prefix="/api/v1", tags=["artifacts"])
PayloadStatus = Literal[
    "scratch", "proposed", "in_review", "approved", "rejected", "deprecated", "archived"
]
Visibility = Literal["project", "private", "restricted"]


class ArtifactCreate(BaseModel):
    type: str
    schema_version: str = "1.0.0"
    title: str = Field(min_length=1, max_length=200)
    body: str = ""
    payload: dict[str, Any]
    visibility: Visibility = "project"
    sensitivity: Sensitivity = Sensitivity.INTERNAL
    owner: str | None = None
    tags: list[str] = Field(default_factory=list)
    locked_fields: list[str] = Field(default_factory=list)


class ArtifactUpdate(BaseModel):
    base_revision: int = Field(ge=1)
    reason: str = Field(min_length=5, max_length=1000)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    body: str | None = None
    payload: dict[str, Any] | None = None
    status: PayloadStatus | None = None
    visibility: Visibility | None = None
    sensitivity: Sensitivity | None = None
    owner: str | None = None
    tags: list[str] | None = None
    locked_fields: list[str] | None = None


class ArtifactRestore(BaseModel):
    base_revision: int = Field(ge=1)
    reason: str = Field(min_length=5, max_length=1000)


class ArtifactPage(BaseModel):
    items: list[Artifact]
    next_cursor: str | None


class RevisionOut(BaseModel):
    id: str
    artifact_id: str
    revision: int
    snapshot: dict[str, Any]
    change_summary: str | None
    actor_id: str
    run_id: str | None
    created_at: datetime


class RevisionDiffField(BaseModel):
    path: str
    before: Any
    after: Any


class RevisionDiffOut(BaseModel):
    artifact_id: str
    from_revision: int
    to_revision: int
    changes: list[RevisionDiffField]


def as_contract(record: ArtifactRecord) -> Artifact:
    return Artifact.model_validate(
        {
            "id": record.id,
            "alias": record.alias,
            "project_id": record.project_id,
            "type": record.type,
            "schema_version": record.schema_version,
            "title": record.title,
            "body": record.body,
            "payload": record.payload,
            "status": record.status,
            "revision": record.revision,
            "created_by": record.created_by,
            "updated_by": record.updated_by,
            "provenance": record.provenance,
            "visibility": record.visibility,
            "sensitivity": record.sensitivity,
            "owner": record.owner,
            "tags": record.tags,
            "locked_fields": record.locked_fields,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
        }
    )


async def project_for_write(db: AsyncSession, project_id: str) -> Project:
    project = await db.scalar(
        select(Project)
        .where(Project.id == project_id, Project.status == "active")
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


async def artifact_for_member(
    db: AsyncSession, artifact_id: str, user_id: str, *, lock: bool = False
) -> tuple[ArtifactRecord, Project, WorkspaceMember]:
    statement = select(ArtifactRecord).where(
        ArtifactRecord.id == artifact_id, ArtifactRecord.deleted_at.is_(None)
    )
    if lock:
        statement = statement.with_for_update()
    artifact = await db.scalar(statement)
    if artifact is None:
        raise HTTPException(status_code=404, detail="Artifact not found")
    project = await db.get(Project, artifact.project_id)
    if project is None or project.status != "active":
        raise HTTPException(status_code=404, detail="Artifact not found")
    member = await membership(db, project.workspace_id, user_id)
    return artifact, project, member


def validate_contract(record: ArtifactRecord) -> Artifact:
    try:
        return as_contract(record)
    except ValidationError as exc:
        details = [
            {
                "loc": [str(part) for part in issue.get("loc", ())],
                "message": str(issue.get("msg", "Invalid value")),
                "code": str(issue.get("type", "value_error")),
            }
            for issue in exc.errors()
        ]
        raise HTTPException(
            status_code=422,
            detail={
                "code": "artifact.validation",
                "message": "Artifact validation failed",
                "details": {"issues": details},
            },
        ) from exc


def status_transition(current: str, requested: str) -> None:
    allowed: dict[str, set[str]] = {
        "scratch": {"proposed"},
        "proposed": {"in_review"},
        "in_review": {"approved", "rejected"},
        "approved": {"deprecated"},
        "rejected": {"proposed"},
        "deprecated": set(),
    }
    if requested != current and requested not in allowed.get(current, set()):
        raise HTTPException(
            status_code=409,
            detail={
                "code": "conflict.invalid_transition",
                "message": f"Cannot change artifact status from {current} to {requested}",
                "details": {"from": current, "to": requested},
            },
        )


def check_base_revision(expected: int, actual: int) -> None:
    if expected != actual:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "conflict.stale_revision",
                "message": "Artifact revision has changed",
                "details": {"expected_revision": expected, "current_revision": actual},
            },
        )


async def record_artifact_change(
    db: AsyncSession,
    request: Request,
    artifact: ArtifactRecord,
    project: Project,
    actor: str,
    *,
    event_type: str,
    reason: str,
    run_id: str | None = None,
) -> Artifact:
    artifact.updated_by = actor
    artifact.revision += 1
    artifact.updated_at = datetime.now(UTC)
    project.current_revision += 1
    contract = validate_contract(artifact)
    await db.flush()
    db.add(
        ArtifactRevisionRecord(
            id=new_ulid(),
            artifact_id=artifact.id,
            revision=artifact.revision,
            snapshot=contract.model_dump(mode="json"),
            change_summary=reason,
            actor_id=actor,
            run_id=run_id,
        )
    )
    db.add(
        ProjectEvent(
            id=new_ulid(),
            project_id=project.id,
            revision=project.current_revision,
            event_type=event_type,
            payload={"artifact_id": artifact.id, "artifact_revision": artifact.revision},
            actor_id=actor,
            correlation_id=correlation_id(request),
        )
    )
    audit(
        db,
        request,
        actor,
        project.workspace_id,
        event_type,
        "artifact",
        artifact.id,
        reason,
    )
    return contract


@router.post("/projects/{project_id}/artifacts", response_model=Artifact, status_code=201)
async def create_artifact(
    project_id: str,
    payload: ArtifactCreate,
    request: Request,
    user: str = Depends(session_user),
    db: AsyncSession = Depends(db_session),
) -> Artifact:
    project = await project_for_write(db, project_id)
    member = await membership(db, project.workspace_id, user)
    require_role(member, "owner", "editor")
    now = datetime.now(UTC)
    provenance = Provenance(origin=ProvenanceOrigin.USER_INPUT)
    provisional = Artifact(
        id="art_01JG7Z3M8Q9XR4T2V6B0N5K1D9",
        alias="TMP-000",
        project_id=project_id,
        type=payload.type,
        schema_version=payload.schema_version,
        title=payload.title,
        body=payload.body,
        payload=payload.payload,
        status=ArtifactStatus.SCRATCH,
        revision=1,
        created_by=user,
        updated_by=user,
        provenance=provenance,
        visibility=payload.visibility,
        sensitivity=payload.sensitivity,
        owner=payload.owner,
        tags=payload.tags,
        locked_fields=payload.locked_fields,
        created_at=now,
        updated_at=now,
    )
    artifact_id, alias = await allocate_artifact_identity(
        db, project_id=project_id, artifact_type=payload.type
    )
    project.current_revision += 1
    record = ArtifactRecord(
        id=artifact_id,
        project_id=project_id,
        alias=alias,
        type=payload.type,
        schema_version=payload.schema_version,
        title=payload.title,
        body=payload.body,
        payload=payload.payload,
        status=provisional.status.value,
        revision=1,
        created_by=user,
        updated_by=user,
        provenance=provisional.provenance.model_dump(mode="json"),
        visibility=payload.visibility,
        sensitivity=payload.sensitivity.value,
        locked_fields=payload.locked_fields,
        owner=payload.owner,
        tags=payload.tags,
        created_at=now,
        updated_at=now,
    )
    db.add(record)
    await db.flush()
    contract = validate_contract(record)
    db.add(
        ArtifactRevisionRecord(
            id=new_ulid(),
            artifact_id=artifact_id,
            revision=1,
            snapshot=contract.model_dump(mode="json"),
            change_summary="Artifact created",
            actor_id=user,
        )
    )
    db.add(
        ProjectEvent(
            id=new_ulid(),
            project_id=project_id,
            revision=project.current_revision,
            event_type="artifact.created",
            payload={"artifact_id": artifact_id, "artifact_revision": 1},
            actor_id=user,
            correlation_id=correlation_id(request),
        )
    )
    audit(
        db,
        request,
        user,
        project.workspace_id,
        "artifact.created",
        "artifact",
        artifact_id,
        "Artifact created",
    )
    await db.commit()
    await db.refresh(record)
    return as_contract(record)


@router.get("/projects/{project_id}/artifacts", response_model=ArtifactPage)
async def list_artifacts(
    project_id: str,
    artifact_type: str | None = Query(default=None, alias="type"),
    status: str | None = None,
    q: str | None = Query(default=None, min_length=1, max_length=200),
    cursor: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    user: str = Depends(session_user),
    db: AsyncSession = Depends(db_session),
) -> ArtifactPage:
    project = await db.get(Project, project_id)
    if project is None or project.status != "active":
        raise HTTPException(status_code=404, detail="Project not found")
    await membership(db, project.workspace_id, user)
    statement = select(ArtifactRecord).where(
        ArtifactRecord.project_id == project_id,
        ArtifactRecord.deleted_at.is_(None),
    )
    if artifact_type is not None:
        statement = statement.where(ArtifactRecord.type == artifact_type)
    if status is not None:
        statement = statement.where(ArtifactRecord.status == status)
    if q is not None:
        search_query = func.plainto_tsquery("english", q)
        statement = statement.where(
            or_(
                ArtifactRecord.search_vector.op("@@")(search_query),
                ArtifactRecord.title.op("%")(q),
            )
        )
    if cursor is not None:
        cursor_record = await db.scalar(
            select(ArtifactRecord).where(
                ArtifactRecord.id == cursor,
                ArtifactRecord.project_id == project_id,
                ArtifactRecord.deleted_at.is_(None),
            )
        )
        if cursor_record is None:
            raise HTTPException(status_code=400, detail="Invalid artifact cursor")
        statement = statement.where(
            tuple_(ArtifactRecord.created_at, ArtifactRecord.id)
            > tuple_(cursor_record.created_at, cursor_record.id)
        )
    records = list(
        await db.scalars(
            statement.order_by(ArtifactRecord.created_at, ArtifactRecord.id).limit(limit + 1)
        )
    )
    has_more = len(records) > limit
    page = records[:limit]
    return ArtifactPage(
        items=[as_contract(record) for record in page],
        next_cursor=page[-1].id if has_more and page else None,
    )


@router.get("/artifacts/{artifact_id}", response_model=Artifact)
async def get_artifact(
    artifact_id: str,
    user: str = Depends(session_user),
    db: AsyncSession = Depends(db_session),
) -> Artifact:
    artifact, _, _ = await artifact_for_member(db, artifact_id, user)
    return as_contract(artifact)


@router.get("/artifacts/{artifact_id}/revisions", response_model=list[RevisionOut])
async def list_artifact_revisions(
    artifact_id: str,
    user: str = Depends(session_user),
    db: AsyncSession = Depends(db_session),
) -> list[ArtifactRevisionRecord]:
    artifact, _, _ = await artifact_for_member(db, artifact_id, user)
    result = await db.scalars(
        select(ArtifactRevisionRecord)
        .where(ArtifactRevisionRecord.artifact_id == artifact.id)
        .order_by(ArtifactRevisionRecord.revision)
    )
    return list(result)


def _snapshot_diff(before: Any, after: Any, path: str = "") -> list[RevisionDiffField]:
    if isinstance(before, dict) and isinstance(after, dict):
        changes: list[RevisionDiffField] = []
        for key in sorted(before.keys() | after.keys()):
            child_path = f"{path}.{key}" if path else key
            if key not in before:
                changes.append(RevisionDiffField(path=child_path, before=None, after=after[key]))
            elif key not in after:
                changes.append(RevisionDiffField(path=child_path, before=before[key], after=None))
            else:
                changes.extend(_snapshot_diff(before[key], after[key], child_path))
        return changes
    if before != after:
        return [RevisionDiffField(path=path or "$", before=before, after=after)]
    return []


@router.get("/artifacts/{artifact_id}/diff", response_model=RevisionDiffOut)
async def diff_artifact_revisions(
    artifact_id: str,
    from_revision: int = Query(ge=1),
    to_revision: int = Query(ge=1),
    user: str = Depends(session_user),
    db: AsyncSession = Depends(db_session),
) -> RevisionDiffOut:
    artifact, _, _ = await artifact_for_member(db, artifact_id, user)
    revisions = list(
        await db.scalars(
            select(ArtifactRevisionRecord).where(
                ArtifactRevisionRecord.artifact_id == artifact.id,
                ArtifactRevisionRecord.revision.in_([from_revision, to_revision]),
            )
        )
    )
    by_revision = {revision.revision: revision for revision in revisions}
    if from_revision not in by_revision or to_revision not in by_revision:
        raise HTTPException(status_code=404, detail="Artifact revision not found")
    return RevisionDiffOut(
        artifact_id=artifact.id,
        from_revision=from_revision,
        to_revision=to_revision,
        changes=_snapshot_diff(
            by_revision[from_revision].snapshot,
            by_revision[to_revision].snapshot,
        ),
    )


@router.post("/artifacts/{artifact_id}/revisions/{revision}/restore", response_model=Artifact)
async def restore_artifact_revision(
    artifact_id: str,
    revision: int,
    request: Request,
    base_revision: int = Query(ge=1),
    reason: str = Query(min_length=5, max_length=1000),
    user: str = Depends(session_user),
    db: AsyncSession = Depends(db_session),
) -> Artifact:
    artifact, project, member = await artifact_for_member(db, artifact_id, user, lock=True)
    require_role(member, "owner", "editor")
    check_base_revision(base_revision, artifact.revision)
    await project_for_write(db, project.id)
    snapshot = await db.scalar(
        select(ArtifactRevisionRecord).where(
            ArtifactRevisionRecord.artifact_id == artifact.id,
            ArtifactRevisionRecord.revision == revision,
        )
    )
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Artifact revision not found")
    state = Artifact.model_validate(snapshot.snapshot)
    for name in (
        "type",
        "schema_version",
        "title",
        "body",
        "payload",
        "status",
        "provenance",
        "visibility",
        "sensitivity",
        "locked_fields",
        "owner",
        "tags",
    ):
        setattr(artifact, name, getattr(state, name))
    artifact.provenance = state.provenance.model_dump(mode="json")
    artifact.deleted_at = None
    artifact.archived_from_status = None
    result = await record_artifact_change(
        db,
        request,
        artifact,
        project,
        user,
        event_type="artifact.restored",
        reason=f"{reason} (restored from revision {revision})",
    )
    await db.commit()
    await db.refresh(artifact)
    return result


@router.patch("/artifacts/{artifact_id}", response_model=Artifact)
async def update_artifact(
    artifact_id: str,
    payload: ArtifactUpdate,
    request: Request,
    user: str = Depends(session_user),
    db: AsyncSession = Depends(db_session),
) -> Artifact:
    artifact, project, member = await artifact_for_member(db, artifact_id, user, lock=True)
    require_role(member, "owner", "editor")
    check_base_revision(payload.base_revision, artifact.revision)
    await project_for_write(db, project.id)
    changes = payload.model_dump(exclude_unset=True, exclude={"base_revision", "reason"})
    requested_status = changes.pop("status", None)
    if requested_status is not None:
        status_transition(artifact.status, requested_status)
        artifact.status = requested_status
    for name, value in changes.items():
        setattr(artifact, name, value)
    event_type = "artifact.updated"
    if requested_status == "approved":
        event_type = "artifact.approved"
    elif requested_status == "rejected":
        event_type = "artifact.rejected"
    await record_artifact_change(
        db,
        request,
        artifact,
        project,
        user,
        event_type=event_type,
        reason=payload.reason,
    )
    await db.commit()
    await db.refresh(artifact)
    return as_contract(artifact)


@router.delete("/artifacts/{artifact_id}", response_model=Artifact)
async def archive_artifact(
    artifact_id: str,
    request: Request,
    base_revision: int = Query(ge=1),
    reason: str = Query(min_length=5, max_length=1000),
    user: str = Depends(session_user),
    db: AsyncSession = Depends(db_session),
) -> Artifact:
    artifact, project, member = await artifact_for_member(db, artifact_id, user, lock=True)
    require_role(member, "owner", "editor")
    check_base_revision(base_revision, artifact.revision)
    await project_for_write(db, project.id)
    artifact.archived_from_status = artifact.status
    artifact.status = "archived"
    artifact.deleted_at = datetime.now(UTC)
    result = await record_artifact_change(
        db,
        request,
        artifact,
        project,
        user,
        event_type="artifact.archived",
        reason=reason,
    )
    await db.commit()
    return result


@router.post("/artifacts/{artifact_id}/restore", response_model=Artifact)
async def restore_artifact(
    artifact_id: str,
    payload: ArtifactRestore,
    request: Request,
    user: str = Depends(session_user),
    db: AsyncSession = Depends(db_session),
) -> Artifact:
    artifact = await db.scalar(
        select(ArtifactRecord).where(ArtifactRecord.id == artifact_id).with_for_update()
    )
    if artifact is None or artifact.status != "archived" or artifact.deleted_at is None:
        raise HTTPException(status_code=404, detail="Archived artifact not found")
    project = await db.get(Project, artifact.project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Artifact not found")
    member = await membership(db, project.workspace_id, user)
    require_role(member, "owner", "editor")
    check_base_revision(payload.base_revision, artifact.revision)
    await project_for_write(db, project.id)
    artifact.status = artifact.archived_from_status or "scratch"
    artifact.archived_from_status = None
    artifact.deleted_at = None
    result = await record_artifact_change(
        db,
        request,
        artifact,
        project,
        user,
        event_type="artifact.restored",
        reason=payload.reason,
    )
    await db.commit()
    return result
