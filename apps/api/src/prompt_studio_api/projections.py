from __future__ import annotations

import json

# FastAPI uses Depends markers as parameter defaults by design.
# ruff: noqa: B008
from datetime import UTC, datetime
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.artifacts.models import ArtifactRecord, ArtifactRevisionRecord
from backend.app.canvas.layout import AutoLayoutPolicy, auto_layout, snap_layout
from backend.app.canvas.models import ProjectionLayoutOperation, ProjectionRecord
from backend.app.canvas.projections import semantic_hash_for_artifact
from backend.app.graph.models import ArtifactEdge
from backend.app.ids import allocate_artifact_identity, new_ulid
from backend.app.projects.models import Project, ProjectEvent
from prompt_studio_api.artifacts import validate_contract
from prompt_studio_api.contracts.artifact import (
    ArtifactStatus,
    Provenance,
    ProvenanceOrigin,
    Sensitivity,
)
from prompt_studio_api.contracts.registry import validate_edge_pair
from prompt_studio_api.graph_queries import project_membership
from prompt_studio_api.workspaces import (
    audit,
    correlation_id,
    db_session,
    membership,
    require_role,
    session_user,
)

router = APIRouter(prefix="/api/v1/projects/{project_id}/projections", tags=["canvas"])


class FrameSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=120)
    order: int = Field(ge=0)
    stage_binding: str | None = None
    scope_filter: list[str] = Field(default_factory=list, max_length=50)
    auto_layout_policy: Literal["free", "grid", "column", "tree"] = "free"


class ProjectionPosition(BaseModel):
    model_config = ConfigDict(extra="forbid")
    x: float = Field(ge=-100_000, le=100_000, allow_inf_nan=False)
    y: float = Field(ge=-100_000, le=100_000, allow_inf_nan=False)
    w: float = Field(gt=0, le=20_000, allow_inf_nan=False)
    h: float = Field(gt=0, le=20_000, allow_inf_nan=False)
    z: int = Field(ge=-1_000_000, le=1_000_000)
    angle: float = Field(default=0, ge=-360, le=360, allow_inf_nan=False)


class ProjectionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    view_id: str = Field(min_length=1, max_length=128)
    artifact_id: str | None = None
    engine: Literal["excalidraw"] = "excalidraw"
    engine_element_ids: list[str] = Field(default_factory=list, max_length=100)
    visual_type: Literal["typed_card", "screen", "diagram", "sketch", "image", "frame"]
    position: ProjectionPosition
    style: dict[str, Any] = Field(default_factory=dict)
    frame_id: str | None = None
    frame_settings: FrameSettings | None = None
    collapsed: bool = False
    locked: bool = False

    @model_validator(mode="after")
    def validate_frame(self) -> ProjectionCreate:
        if self.visual_type == "frame" and self.frame_settings is None:
            raise ValueError("Frame projections need frame settings")
        if self.visual_type != "frame" and self.frame_settings is not None:
            raise ValueError("Frame settings are only valid for frame projections")
        return self


class ProjectionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    base_layout_revision: int = Field(ge=0)
    position: ProjectionPosition | None = None
    style: dict[str, Any] | None = None
    frame_id: str | None = None
    frame_settings: FrameSettings | None = None
    collapsed: bool | None = None
    locked: bool | None = None


class AutoLayoutRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    base_layout_revision: int = Field(ge=0)
    projection_ids: list[str] = Field(min_length=1, max_length=500)
    policy: AutoLayoutPolicy
    frame_id: str | None = None
    gap: float = Field(default=32, ge=0, le=1000, allow_inf_nan=False)
    snap_to_grid: bool = True
    grid_size: float = Field(default=16, gt=0, le=512, allow_inf_nan=False)


class AutoLayoutOut(BaseModel):
    operation_id: str
    layout_revision: int
    positions: dict[str, dict[str, Any]]


class UndoLayoutRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    base_layout_revision: int = Field(ge=0)


class SketchPromotionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    base_revision: int = Field(ge=0)
    scene_json: str = Field(min_length=2, max_length=2_000_000)
    artifact_type: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    title: str = Field(min_length=1, max_length=200)
    body: str = ""
    payload: dict[str, Any]


class SketchPromotionOut(BaseModel):
    sketch_artifact_id: str
    artifact_id: str
    edge_id: str
    project_revision: int


class ZoneOut(BaseModel):
    id: str
    title: str
    order: int
    stage_binding: str | None
    scope_filter: list[str]
    auto_layout_policy: AutoLayoutPolicy


class ProjectionOut(BaseModel):
    id: str
    project_id: str
    view_id: str
    artifact_id: str | None
    engine: str
    engine_element_ids: list[str]
    visual_type: str
    position: dict[str, Any]
    style: dict[str, Any]
    frame_id: str | None
    frame_settings: dict[str, Any] | None
    collapsed: bool
    locked: bool
    semantic_hash: str | None
    layout_revision: int
    updated_at: datetime


DEFAULT_PROJECT_ZONES = [
    ZoneOut(
        id="discovery",
        title="Discovery",
        order=1,
        stage_binding="S1_capture",
        scope_filter=["brief", "idea", "problem", "persona"],  # noqa: E501
        auto_layout_policy="free",
    ),
    ZoneOut(
        id="requirements",
        title="Requirements",
        order=2,
        stage_binding="S2_define",
        scope_filter=["user_story", "requirement", "constraint", "decision"],  # noqa: E501
        auto_layout_policy="grid",
    ),
    ZoneOut(
        id="ux",
        title="UX",
        order=3,
        stage_binding="S3_experience",
        scope_filter=["user_flow", "screen", "interaction"],  # noqa: E501
        auto_layout_policy="grid",
    ),
    ZoneOut(
        id="architecture",
        title="Architecture",
        order=4,
        stage_binding="S4_architecture",
        scope_filter=["component", "integration"],  # noqa: E501
        auto_layout_policy="tree",
    ),
    ZoneOut(
        id="data-api",
        title="Data / API",
        order=5,
        stage_binding="S4_architecture",
        scope_filter=["data_entity", "api_endpoint", "event_contract"],  # noqa: E501
        auto_layout_policy="grid",
    ),
    ZoneOut(
        id="prompt-lab",
        title="Prompt Lab",
        order=6,
        stage_binding="S5_prompts",
        scope_filter=["prompt", "prompt_flow", "skill"],  # noqa: E501
        auto_layout_policy="grid",
    ),
    ZoneOut(
        id="quality",
        title="Quality",
        order=7,
        stage_binding="S6_quality",
        scope_filter=["risk", "test_case", "evaluation_case"],  # noqa: E501
        auto_layout_policy="grid",
    ),
    ZoneOut(
        id="delivery",
        title="Delivery",
        order=8,
        stage_binding="S7_delivery",
        scope_filter=["epic", "task", "milestone"],  # noqa: E501
        auto_layout_policy="tree",
    ),
    ZoneOut(
        id="open-questions",
        title="Open Questions",
        order=9,
        stage_binding=None,
        scope_filter=["question", "issue"],  # noqa: E501
        auto_layout_policy="column",
    ),
]


async def _editable_project(db: AsyncSession, project_id: str, user: str) -> tuple[Project, Any]:
    project = await project_membership(db, project_id, user)
    member = await membership(db, project.workspace_id, user)
    require_role(member, "owner", "editor")
    locked = await db.scalar(
        select(Project)
        .where(Project.id == project.id, Project.status == "active")
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if locked is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return locked, member


async def _projection_for_project(
    db: AsyncSession, project_id: str, projection_id: str
) -> ProjectionRecord:
    projection = await db.scalar(
        select(ProjectionRecord).where(
            ProjectionRecord.id == projection_id,
            ProjectionRecord.project_id == project_id,
        )
    )
    if projection is None:
        raise HTTPException(status_code=404, detail="Projection not found")
    return projection


@router.post("/{projection_id}/promote", response_model=SketchPromotionOut, status_code=201)
async def promote_sketch(
    project_id: str,
    projection_id: str,
    payload: SketchPromotionRequest,
    request: Request,
    user: str = Depends(session_user),
    db: AsyncSession = Depends(db_session),
) -> SketchPromotionOut:
    project, _ = await _editable_project(db, project_id, user)
    if project.current_revision != payload.base_revision:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "conflict.stale_revision",
                "message": "Project changed since the sketch was selected",
            },
        )
    projection = await _projection_for_project(db, project_id, projection_id)
    if projection.visual_type != "sketch" or projection.artifact_id is not None:
        raise HTTPException(status_code=409, detail="Projection is not an unpromoted sketch")
    try:
        scene = json.loads(payload.scene_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=422, detail="Sketch scene must be valid JSON") from exc
    if not isinstance(scene, dict) or scene.get("type") != "excalidraw":
        raise HTTPException(status_code=422, detail="Sketch scene must be an Excalidraw scene")

    now = datetime.now(UTC)

    async def add_artifact(
        artifact_type: str, title: str, body: str, artifact_payload: dict[str, Any]
    ) -> ArtifactRecord:
        artifact_id, alias = await allocate_artifact_identity(
            db, project_id=project_id, artifact_type=artifact_type
        )
        provenance = Provenance(origin=ProvenanceOrigin.USER_INPUT)
        record = ArtifactRecord(
            id=artifact_id,
            project_id=project_id,
            alias=alias,
            type=artifact_type,
            schema_version="1.0.0",
            title=title,
            body=body,
            payload=artifact_payload,
            status=ArtifactStatus.SCRATCH.value,
            revision=1,
            created_by=user,
            updated_by=user,
            provenance=provenance.model_dump(mode="json"),
            visibility="project",
            sensitivity=Sensitivity.INTERNAL.value,
            locked_fields=[],
            owner=None,
            tags=[],
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
                change_summary="Artifact promoted from canvas sketch",
                actor_id=user,
            )
        )
        project.current_revision += 1
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
            "Artifact promoted from canvas sketch",
        )
        return record

    sketch = await add_artifact(
        "note",
        f"Sketch {projection_id[:8]}",
        "Canvas sketch source",
        {"content": payload.scene_json},
    )
    artifact = await add_artifact(
        payload.artifact_type, payload.title, payload.body, payload.payload
    )
    try:
        validate_edge_pair("derived_from", artifact.type, sketch.type)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    edge = ArtifactEdge(
        id=new_ulid(),
        project_id=project_id,
        source_id=artifact.id,
        target_id=sketch.id,
        edge_type="derived_from",
        edge_metadata={"source_projection_id": projection_id},
        created_by=user,
    )
    db.add(edge)
    await db.flush()
    project.current_revision += 1
    db.add(
        ProjectEvent(
            id=new_ulid(),
            project_id=project_id,
            revision=project.current_revision,
            event_type="edge.created",
            payload={"edge_id": edge.id, "edge_type": "derived_from"},
            actor_id=user,
            correlation_id=correlation_id(request),
        )
    )
    audit(
        db,
        request,
        user,
        project.workspace_id,
        "edge.created",
        "edge",
        edge.id,
        "Promoted artifact derived from canvas sketch",
    )
    projection.artifact_id = sketch.id
    projection.semantic_hash = semantic_hash_for_artifact(sketch)
    projection.style = {**projection.style, "scene_json": payload.scene_json}
    await db.commit()
    return SketchPromotionOut(
        sketch_artifact_id=sketch.id,
        artifact_id=artifact.id,
        edge_id=edge.id,
        project_revision=project.current_revision,
    )


@router.get("", response_model=list[ProjectionOut])
async def list_projections(
    project_id: str,
    view_id: str | None = None,
    user: str = Depends(session_user),
    db: AsyncSession = Depends(db_session),
) -> list[ProjectionRecord]:
    await project_membership(db, project_id, user)
    statement = select(ProjectionRecord).where(ProjectionRecord.project_id == project_id)
    if view_id is not None:
        statement = statement.where(ProjectionRecord.view_id == view_id)
    return list(await db.scalars(statement.order_by(ProjectionRecord.view_id, ProjectionRecord.id)))


@router.get("/default-zones", response_model=list[ZoneOut])
async def default_project_zones(
    project_id: str,
    user: str = Depends(session_user),
    db: AsyncSession = Depends(db_session),
) -> list[ZoneOut]:
    await project_membership(db, project_id, user)
    return DEFAULT_PROJECT_ZONES


@router.post("/auto-layout", response_model=AutoLayoutOut)
async def apply_auto_layout(
    project_id: str,
    payload: AutoLayoutRequest,
    request: Request,
    user: str = Depends(session_user),
    db: AsyncSession = Depends(db_session),
) -> AutoLayoutOut:
    project, _member = await _editable_project(db, project_id, user)
    if payload.base_layout_revision != project.layout_revision:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "conflict.stale_layout_revision",
                "message": "Project layout has changed",
                "details": {
                    "expected_revision": payload.base_layout_revision,
                    "current_revision": project.layout_revision,
                },
            },
        )
    records = list(
        await db.scalars(
            select(ProjectionRecord)
            .where(
                ProjectionRecord.project_id == project.id,
                ProjectionRecord.id.in_(payload.projection_ids),
            )
            .order_by(ProjectionRecord.id)
        )
    )
    if len(records) != len(set(payload.projection_ids)):
        raise HTTPException(status_code=404, detail="One or more projections were not found")
    if payload.frame_id and any(record.frame_id != payload.frame_id for record in records):
        raise HTTPException(
            status_code=422, detail="All projections must belong to the selected frame"
        )
    before_positions = {record.id: dict(record.position) for record in records}
    layout_items = [
        {
            "projection_id": record.id,
            "artifact_id": record.artifact_id,
            "x": float(record.position["x"]),
            "y": float(record.position["y"]),
            "width": float(record.position["w"]),
            "height": float(record.position["h"]),
            "z": int(record.position["z"]),
        }
        for record in records
    ]
    result = auto_layout(layout_items, payload.policy, payload.gap)
    if payload.snap_to_grid:
        result = snap_layout(result, payload.grid_size)
    project.layout_revision += 1
    after_positions: dict[str, dict[str, Any]] = {}
    for item in result:
        record = next(candidate for candidate in records if candidate.id == item["projection_id"])
        position = {
            **record.position,
            "x": item["x"],
            "y": item["y"],
            "w": item["width"],
            "h": item["height"],
            "z": item["z"],
        }
        record.position = position
        record.layout_revision = project.layout_revision
        record.updated_by = user
        record.updated_at = datetime.now(UTC)
        after_positions[record.id] = position
    operation = ProjectionLayoutOperation(
        id=f"lop_{new_ulid()}",
        project_id=project.id,
        layout_revision=project.layout_revision,
        operation_kind=f"auto_layout:{payload.policy}",
        before_positions=before_positions,
        after_positions=after_positions,
        created_by=user,
    )
    db.add(operation)
    audit(
        db,
        request,
        user,
        project.workspace_id,
        "projection.auto_layout",
        "layout_operation",
        operation.id,
        f"Applied {payload.policy} layout to {len(records)} projections",
    )
    await db.commit()
    return AutoLayoutOut(
        operation_id=operation.id,
        layout_revision=project.layout_revision,
        positions=after_positions,
    )


@router.post("/layout-operations/{operation_id}/undo", response_model=AutoLayoutOut)
async def undo_layout_operation(
    project_id: str,
    operation_id: str,
    payload: UndoLayoutRequest,
    request: Request,
    user: str = Depends(session_user),
    db: AsyncSession = Depends(db_session),
) -> AutoLayoutOut:
    project, _member = await _editable_project(db, project_id, user)
    if payload.base_layout_revision != project.layout_revision:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "conflict.stale_layout_revision",
                "message": "Project layout has changed",
                "details": {
                    "expected_revision": payload.base_layout_revision,
                    "current_revision": project.layout_revision,
                },
            },
        )
    operation = await db.scalar(
        select(ProjectionLayoutOperation)
        .where(
            ProjectionLayoutOperation.id == operation_id,
            ProjectionLayoutOperation.project_id == project.id,
        )
        .with_for_update()
    )
    if operation is None:
        raise HTTPException(status_code=404, detail="Layout operation not found")
    if operation.undone_at is not None or operation.layout_revision != project.layout_revision:
        raise HTTPException(
            status_code=409, detail="Only the latest unapplied layout operation can be undone"
        )
    records = list(
        await db.scalars(
            select(ProjectionRecord).where(
                ProjectionRecord.project_id == project.id,
                ProjectionRecord.id.in_(operation.before_positions),
            )
        )
    )
    if len(records) != len(operation.before_positions):
        raise HTTPException(
            status_code=409, detail="A projection in this layout operation no longer exists"
        )
    project.layout_revision += 1
    restored: dict[str, dict[str, Any]] = {}
    for record in records:
        record.position = dict(operation.before_positions[record.id])
        record.layout_revision = project.layout_revision
        record.updated_by = user
        record.updated_at = datetime.now(UTC)
        restored[record.id] = record.position
    operation.undone_at = datetime.now(UTC)
    audit(
        db,
        request,
        user,
        project.workspace_id,
        "projection.layout_undo",
        "layout_operation",
        operation.id,
        "Undid one canvas layout operation",
    )
    await db.commit()
    return AutoLayoutOut(
        operation_id=operation.id,
        layout_revision=project.layout_revision,
        positions=restored,
    )


@router.post("", response_model=ProjectionOut, status_code=201)
async def create_projection(
    project_id: str,
    payload: ProjectionCreate,
    request: Request,
    user: str = Depends(session_user),
    db: AsyncSession = Depends(db_session),
) -> ProjectionRecord:
    project, _member = await _editable_project(db, project_id, user)
    artifact: ArtifactRecord | None = None
    if payload.artifact_id is not None:
        artifact = await db.scalar(
            select(ArtifactRecord).where(
                ArtifactRecord.id == payload.artifact_id,
                ArtifactRecord.project_id == project.id,
                ArtifactRecord.deleted_at.is_(None),
            )
        )
        if artifact is None:
            raise HTTPException(status_code=404, detail="Artifact not found in this project")
    if payload.frame_id is not None:
        frame = await db.scalar(
            select(ProjectionRecord).where(
                ProjectionRecord.id == payload.frame_id,
                ProjectionRecord.project_id == project.id,
                ProjectionRecord.visual_type == "frame",
            )
        )
        if frame is None:
            raise HTTPException(status_code=404, detail="Frame not found in this project")
    project.layout_revision += 1
    record = ProjectionRecord(
        id=f"pvw_{new_ulid()}",
        project_id=project.id,
        view_id=payload.view_id,
        artifact_id=artifact.id if artifact else None,
        engine=payload.engine,
        engine_element_ids=payload.engine_element_ids,
        visual_type=payload.visual_type,
        position=payload.position.model_dump(mode="json"),
        style=payload.style,
        frame_id=payload.frame_id,
        frame_settings=(
            payload.frame_settings.model_dump(mode="json") if payload.frame_settings else None
        ),
        collapsed=payload.collapsed,
        locked=payload.locked,
        semantic_hash=semantic_hash_for_artifact(artifact) if artifact else None,
        layout_revision=project.layout_revision,
        created_by=user,
        updated_by=user,
    )
    db.add(record)
    audit(
        db,
        request,
        user,
        project.workspace_id,
        "projection.created",
        "projection",
        record.id,
        "Created canvas projection",
    )
    await db.commit()
    await db.refresh(record)
    return record


@router.patch("/{projection_id}", response_model=ProjectionOut)
async def update_projection(
    project_id: str,
    projection_id: str,
    payload: ProjectionUpdate,
    request: Request,
    user: str = Depends(session_user),
    db: AsyncSession = Depends(db_session),
) -> ProjectionRecord:
    project, _member = await _editable_project(db, project_id, user)
    record = await _projection_for_project(db, project.id, projection_id)
    if payload.base_layout_revision != project.layout_revision:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "conflict.stale_layout_revision",
                "message": "Project layout has changed",
                "details": {
                    "expected_revision": payload.base_layout_revision,
                    "current_revision": project.layout_revision,
                },
            },
        )
    changes = payload.model_dump(exclude_unset=True, exclude={"base_layout_revision"})
    if "position" in changes and payload.position is not None:
        record.position = payload.position.model_dump(mode="json")
    for name in ("style", "frame_id", "collapsed", "locked"):
        if name in changes:
            setattr(record, name, changes[name])
    if "frame_settings" in changes:
        if record.visual_type != "frame" and payload.frame_settings is not None:
            raise HTTPException(
                status_code=422, detail="Only frame projections have frame settings"
            )
        record.frame_settings = (
            payload.frame_settings.model_dump(mode="json") if payload.frame_settings else None
        )
    if payload.frame_id is not None:
        frame = await db.scalar(
            select(ProjectionRecord).where(
                ProjectionRecord.id == payload.frame_id,
                ProjectionRecord.project_id == project.id,
                ProjectionRecord.visual_type == "frame",
            )
        )
        if frame is None:
            raise HTTPException(status_code=404, detail="Frame not found in this project")
    project.layout_revision += 1
    record.layout_revision = project.layout_revision
    record.updated_by = user
    record.updated_at = datetime.now(UTC)
    audit(
        db,
        request,
        user,
        project.workspace_id,
        "projection.updated",
        "projection",
        record.id,
        "Updated canvas layout",
    )
    await db.commit()
    await db.refresh(record)
    return record


@router.delete("/{projection_id}", status_code=204)
async def delete_projection(
    project_id: str,
    projection_id: str,
    request: Request,
    base_layout_revision: int = Query(ge=0),
    user: str = Depends(session_user),
    db: AsyncSession = Depends(db_session),
) -> None:
    project, _member = await _editable_project(db, project_id, user)
    record = await _projection_for_project(db, project.id, projection_id)
    if base_layout_revision != project.layout_revision:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "conflict.stale_layout_revision",
                "message": "Project layout has changed",
                "details": {
                    "expected_revision": base_layout_revision,
                    "current_revision": project.layout_revision,
                },
            },
        )
    project.layout_revision += 1
    audit(
        db,
        request,
        user,
        project.workspace_id,
        "projection.deleted",
        "projection",
        record.id,
        "Deleted canvas projection",
    )
    await db.delete(record)
    await db.commit()
