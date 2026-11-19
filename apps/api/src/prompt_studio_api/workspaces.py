from __future__ import annotations

# FastAPI uses Depends markers as parameter defaults by design.
# ruff: noqa: B008
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.identity.models import AuditEvent, Workspace, WorkspaceMember
from backend.app.ids import new_project_id, new_ulid
from backend.app.projects.models import Project, ProjectEvent
from prompt_studio_api.api_errors import request_correlation_id

Role = Literal["owner", "editor", "reviewer", "viewer"]
router = APIRouter(prefix="/api/v1", tags=["workspaces"])


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class WorkspacePatch(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class WorkspaceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    created_at: Any


class MemberCreate(BaseModel):
    user_id: str = Field(min_length=1, max_length=200)
    role: Literal["editor", "reviewer", "viewer"]


class MemberPatch(BaseModel):
    role: Role


class MemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    workspace_id: str
    user_id: str
    role: Role
    status: str


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None


class ProjectPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    workspace_id: str
    name: str
    description: str | None
    status: str
    current_revision: int
    layout_revision: int
    stage: str
    created_by: str


async def session_user(request: Request) -> str:
    session = request.session
    user = session.get("user")
    expires_at = session.get("expires_at")
    if not isinstance(user, dict):
        raise HTTPException(status_code=401, detail="Authentication required")
    subject = user.get("sub")
    if not isinstance(subject, str):
        raise HTTPException(status_code=401, detail="Authentication required")
    if not isinstance(expires_at, int) or expires_at <= int(request.app.state.clock()):
        session.clear()
        raise HTTPException(status_code=401, detail="Authentication required")
    return subject


async def db_session(request: Request, user: str = Depends(session_user)) -> Any:
    factory = request.app.state.db_session_factory
    if factory is None:
        raise HTTPException(status_code=503, detail="Database is not configured")
    async with factory() as session:
        await session.execute(text("SET LOCAL ROLE prompt_studio_app"))
        await session.execute(
            text("SELECT set_config('app.user_id', :user_id, true)"), {"user_id": user}
        )
        yield session


async def membership(db: AsyncSession, workspace_id: str, user_id: str) -> WorkspaceMember:
    member = await db.get(WorkspaceMember, (workspace_id, user_id))
    if member is None or member.status != "active":
        raise HTTPException(status_code=404, detail="Workspace not found")
    return member


def require_role(member: WorkspaceMember, *roles: str) -> None:
    if member.role not in roles:
        raise HTTPException(status_code=403, detail="Insufficient workspace role")


def correlation_id(request: Request) -> str:
    return request_correlation_id(request)


def audit(
    db: AsyncSession,
    request: Request,
    actor: str,
    workspace_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    reason: str,
) -> None:
    db.add(
        AuditEvent(
            id=new_ulid(),
            workspace_id=workspace_id,
            actor_id=actor,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            reason=reason,
            event_metadata={},
            correlation_id=correlation_id(request),
        )
    )


@router.post("/workspaces", response_model=WorkspaceOut, status_code=201)
async def create_workspace(
    payload: WorkspaceCreate,
    request: Request,
    user: str = Depends(session_user),
    db: AsyncSession = Depends(db_session),
) -> Workspace:
    workspace = Workspace(id=new_ulid(), name=payload.name.strip())
    await db.execute(
        text("SELECT set_config('app.workspace_create_id', :workspace_id, true)"),
        {"workspace_id": workspace.id},
    )
    db.add(workspace)
    db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user, role="owner"))
    await db.flush()
    audit(
        db,
        request,
        user,
        workspace.id,
        "workspace.created",
        "workspace",
        workspace.id,
        "Workspace created",
    )
    await db.commit()
    await db.refresh(workspace)
    return workspace


@router.get("/workspaces", response_model=list[WorkspaceOut])
async def list_workspaces(
    user: str = Depends(session_user),
    db: AsyncSession = Depends(db_session),
) -> list[Workspace]:
    result = await db.scalars(
        select(Workspace)
        .join(WorkspaceMember)
        .where(WorkspaceMember.user_id == user, WorkspaceMember.status == "active")
        .order_by(Workspace.created_at)
    )
    return list(result)


@router.get("/workspaces/{workspace_id}", response_model=WorkspaceOut)
async def get_workspace(
    workspace_id: str,
    user: str = Depends(session_user),
    db: AsyncSession = Depends(db_session),
) -> Workspace:
    await membership(db, workspace_id, user)
    workspace = await db.get(Workspace, workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace


@router.patch("/workspaces/{workspace_id}", response_model=WorkspaceOut)
async def update_workspace(
    workspace_id: str,
    payload: WorkspacePatch,
    request: Request,
    user: str = Depends(session_user),
    db: AsyncSession = Depends(db_session),
) -> Workspace:
    member = await membership(db, workspace_id, user)
    require_role(member, "owner")
    workspace = await db.get(Workspace, workspace_id)
    assert workspace is not None
    workspace.name = payload.name.strip()
    audit(
        db,
        request,
        user,
        workspace_id,
        "workspace.updated",
        "workspace",
        workspace_id,
        "Workspace details updated",
    )
    await db.commit()
    await db.refresh(workspace)
    return workspace


@router.get("/workspaces/{workspace_id}/members", response_model=list[MemberOut])
async def list_members(
    workspace_id: str,
    user: str = Depends(session_user),
    db: AsyncSession = Depends(db_session),
) -> list[WorkspaceMember]:
    await membership(db, workspace_id, user)
    result = await db.scalars(
        select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id)
    )
    return list(result)


@router.post("/workspaces/{workspace_id}/members", response_model=MemberOut, status_code=201)
async def add_member(
    workspace_id: str,
    payload: MemberCreate,
    request: Request,
    user: str = Depends(session_user),
    db: AsyncSession = Depends(db_session),
) -> WorkspaceMember:
    member = await membership(db, workspace_id, user)
    require_role(member, "owner")
    if await db.get(WorkspaceMember, (workspace_id, payload.user_id)) is not None:
        raise HTTPException(status_code=409, detail="Workspace member already exists")
    created = WorkspaceMember(workspace_id=workspace_id, user_id=payload.user_id, role=payload.role)
    db.add(created)
    audit(
        db,
        request,
        user,
        workspace_id,
        "member.added",
        "workspace_member",
        payload.user_id,
        "Workspace member added",
    )
    await db.commit()
    await db.refresh(created)
    return created


@router.patch("/workspaces/{workspace_id}/members/{member_id}", response_model=MemberOut)
async def update_member(
    workspace_id: str,
    member_id: str,
    payload: MemberPatch,
    request: Request,
    user: str = Depends(session_user),
    db: AsyncSession = Depends(db_session),
) -> WorkspaceMember:
    owner = await membership(db, workspace_id, user)
    require_role(owner, "owner")
    target = await db.get(WorkspaceMember, (workspace_id, member_id))
    if target is None:
        raise HTTPException(status_code=404, detail="Workspace member not found")
    if target.role == "owner" and payload.role != "owner":
        count = await db.scalar(
            select(func.count())
            .select_from(WorkspaceMember)
            .where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.role == "owner",
                WorkspaceMember.status == "active",
            )
        )
        if count is not None and count <= 1:
            raise HTTPException(status_code=409, detail="Workspace must retain an owner")
    target.role = payload.role
    audit(
        db,
        request,
        user,
        workspace_id,
        "member.role_updated",
        "workspace_member",
        member_id,
        "Workspace member role updated",
    )
    await db.commit()
    await db.refresh(target)
    return target


@router.delete("/workspaces/{workspace_id}/members/{member_id}", status_code=204)
async def suspend_member(
    workspace_id: str,
    member_id: str,
    request: Request,
    user: str = Depends(session_user),
    db: AsyncSession = Depends(db_session),
) -> Response:
    owner = await membership(db, workspace_id, user)
    require_role(owner, "owner")
    target = await db.get(WorkspaceMember, (workspace_id, member_id))
    if target is None:
        raise HTTPException(status_code=404, detail="Workspace member not found")
    if target.status == "suspended":
        return Response(status_code=204)
    if target.role == "owner":
        count = await db.scalar(
            select(func.count())
            .select_from(WorkspaceMember)
            .where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.role == "owner",
                WorkspaceMember.status == "active",
            )
        )
        if count is not None and count <= 1:
            raise HTTPException(status_code=409, detail="Workspace must retain an owner")
    target.status = "suspended"
    audit(
        db,
        request,
        user,
        workspace_id,
        "member.suspended",
        "workspace_member",
        member_id,
        "Workspace member suspended",
    )
    await db.commit()
    return Response(status_code=204)


@router.get("/workspaces/{workspace_id}/projects", response_model=list[ProjectOut])
async def list_projects(
    workspace_id: str,
    user: str = Depends(session_user),
    db: AsyncSession = Depends(db_session),
) -> list[Project]:
    await membership(db, workspace_id, user)
    result = await db.scalars(
        select(Project)
        .where(Project.workspace_id == workspace_id, Project.status == "active")
        .order_by(Project.created_at)
    )
    return list(result)


@router.post("/workspaces/{workspace_id}/projects", response_model=ProjectOut, status_code=201)
async def create_project(
    workspace_id: str,
    payload: ProjectCreate,
    request: Request,
    user: str = Depends(session_user),
    db: AsyncSession = Depends(db_session),
) -> Project:
    member = await membership(db, workspace_id, user)
    require_role(member, "owner", "editor")
    project = Project(
        id=new_project_id(),
        workspace_id=workspace_id,
        name=payload.name.strip(),
        description=payload.description,
        created_by=user,
        current_revision=1,
    )
    db.add(project)
    await db.flush()
    correlation = correlation_id(request)
    db.add(
        ProjectEvent(
            id=new_ulid(),
            project_id=project.id,
            revision=1,
            event_type="project.created",
            payload={"name": project.name},
            actor_id=user,
            correlation_id=correlation,
        )
    )
    audit(
        db, request, user, workspace_id, "project.created", "project", project.id, "Project created"
    )
    await db.commit()
    await db.refresh(project)
    return project


async def project_access(
    db: AsyncSession,
    project_id: str,
    user: str,
) -> tuple[Project, WorkspaceMember]:
    project = await db.get(Project, project_id)
    if project is None or project.status != "active":
        raise HTTPException(status_code=404, detail="Project not found")
    member = await membership(db, project.workspace_id, user)
    return project, member


@router.get("/projects/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: str,
    user: str = Depends(session_user),
    db: AsyncSession = Depends(db_session),
) -> Project:
    project, _ = await project_access(db, project_id, user)
    return project


@router.patch("/projects/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: str,
    payload: ProjectPatch,
    request: Request,
    user: str = Depends(session_user),
    db: AsyncSession = Depends(db_session),
) -> Project:
    project, member = await project_access(db, project_id, user)
    require_role(member, "owner", "editor")
    changes = payload.model_dump(exclude_unset=True)
    for key, value in changes.items():
        if value is not None or key == "description":
            setattr(
                project, key, value.strip() if key == "name" and isinstance(value, str) else value
            )
    if changes:
        project.current_revision += 1
        correlation = correlation_id(request)
        db.add(
            ProjectEvent(
                id=new_ulid(),
                project_id=project.id,
                revision=project.current_revision,
                event_type="project.updated",
                payload=changes,
                actor_id=user,
                correlation_id=correlation,
            )
        )
        audit(
            db,
            request,
            user,
            project.workspace_id,
            "project.updated",
            "project",
            project.id,
            "Project details updated",
        )
    await db.commit()
    await db.refresh(project)
    return project


@router.delete("/projects/{project_id}", status_code=204)
async def archive_project(
    project_id: str,
    request: Request,
    user: str = Depends(session_user),
    db: AsyncSession = Depends(db_session),
) -> Response:
    project, member = await project_access(db, project_id, user)
    require_role(member, "owner", "editor")
    project.status = "archived"
    project.current_revision += 1
    correlation = correlation_id(request)
    db.add(
        ProjectEvent(
            id=new_ulid(),
            project_id=project.id,
            revision=project.current_revision,
            event_type="project.archived",
            payload={},
            actor_id=user,
            correlation_id=correlation,
        )
    )
    audit(
        db,
        request,
        user,
        project.workspace_id,
        "project.archived",
        "project",
        project.id,
        "Project archived",
    )
    await db.commit()
    return Response(status_code=204)
