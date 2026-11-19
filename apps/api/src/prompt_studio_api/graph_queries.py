from __future__ import annotations

# FastAPI uses Depends markers as parameter defaults by design.
# ruff: noqa: B008
from collections import deque
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.artifacts.models import ArtifactRecord
from backend.app.graph.models import ArtifactEdge
from backend.app.projects.models import Project
from prompt_studio_api.artifacts import as_contract
from prompt_studio_api.contracts.artifact import Artifact
from prompt_studio_api.edges import EdgeOut
from prompt_studio_api.workspaces import db_session, membership, session_user

router = APIRouter(prefix="/api/v1/projects/{project_id}/graph", tags=["graph"])
Direction = Literal["outgoing", "incoming", "both"]
NODE_LIMIT = 500


class GraphNode(BaseModel):
    artifact: Artifact
    depth: int


class NeighborhoodResult(BaseModel):
    root_id: str
    max_depth: int
    nodes: list[GraphNode]
    edges: list[EdgeOut]
    truncated: bool


class ImpactResult(BaseModel):
    root_id: str
    max_depth: int
    affected: list[GraphNode]
    truncated: bool


class TraceabilityResult(BaseModel):
    requirement: Artifact
    screens: list[Artifact]
    components: list[Artifact]
    apis: list[Artifact]
    tests: list[Artifact]
    tasks: list[Artifact]
    gaps: list[str]


async def project_membership(db: AsyncSession, project_id: str, user_id: str) -> Project:
    project = await db.get(Project, project_id)
    if project is None or project.status != "active":
        raise HTTPException(status_code=404, detail="Project not found")
    await membership(db, project.workspace_id, user_id)
    return project


async def load_project_graph(
    db: AsyncSession, project_id: str
) -> tuple[dict[str, ArtifactRecord], list[ArtifactEdge]]:
    records = await db.scalars(
        select(ArtifactRecord).where(
            ArtifactRecord.project_id == project_id,
            ArtifactRecord.deleted_at.is_(None),
        )
    )
    edges = await db.scalars(select(ArtifactEdge).where(ArtifactEdge.project_id == project_id))
    return {record.id: record for record in records}, list(edges)


def edge_out(edge: ArtifactEdge) -> EdgeOut:
    return EdgeOut(
        id=edge.id,
        project_id=edge.project_id,
        source_id=edge.source_id,
        target_id=edge.target_id,
        edge_type=edge.edge_type,
        metadata=edge.edge_metadata,
        created_by=edge.created_by,
        created_at=edge.created_at,
    )


def get_root(records: dict[str, ArtifactRecord], artifact_id: str) -> ArtifactRecord:
    root = records.get(artifact_id)
    if root is None:
        raise HTTPException(status_code=404, detail="Artifact not found in this project")
    return root


def traverse(
    records: dict[str, ArtifactRecord],
    edges: list[ArtifactEdge],
    *,
    root_id: str,
    depth_limit: int,
    direction: Direction,
    edge_types: set[str] | None = None,
) -> tuple[dict[str, int], list[ArtifactEdge], bool]:
    depths = {root_id: 0}
    pending: deque[str] = deque([root_id])
    traversed: dict[str, ArtifactEdge] = {}
    truncated = False
    while pending:
        current = pending.popleft()
        depth = depths[current]
        if depth >= depth_limit:
            continue
        for edge in edges:
            if edge_types is not None and edge.edge_type not in edge_types:
                continue
            if direction == "outgoing" and edge.source_id == current:
                neighbor = edge.target_id
            elif direction == "incoming" and edge.target_id == current:
                neighbor = edge.source_id
            elif direction == "both" and current in {edge.source_id, edge.target_id}:
                neighbor = edge.target_id if edge.source_id == current else edge.source_id
            else:
                continue
            if neighbor not in records:
                continue
            traversed[edge.id] = edge
            if neighbor not in depths:
                if len(depths) >= NODE_LIMIT:
                    truncated = True
                    continue
                depths[neighbor] = depth + 1
                pending.append(neighbor)
    return (
        depths,
        sorted(traversed.values(), key=lambda edge: (edge.created_at, edge.id)),
        truncated,
    )


@router.get("/neighborhood", response_model=NeighborhoodResult)
async def neighborhood(
    project_id: str,
    artifact_id: str,
    depth: int = Query(default=1, ge=1, le=5),
    direction: Direction = "both",
    edge_type: list[str] | None = Query(default=None),
    user: str = Depends(session_user),
    db: AsyncSession = Depends(db_session),
) -> NeighborhoodResult:
    await project_membership(db, project_id, user)
    records, edges = await load_project_graph(db, project_id)
    get_root(records, artifact_id)
    depths, traversed, truncated = traverse(
        records,
        edges,
        root_id=artifact_id,
        depth_limit=depth,
        direction=direction,
        edge_types=set(edge_type) if edge_type else None,
    )
    return NeighborhoodResult(
        root_id=artifact_id,
        max_depth=depth,
        nodes=[
            GraphNode(artifact=as_contract(records[node_id]), depth=node_depth)
            for node_id, node_depth in sorted(depths.items(), key=lambda item: (item[1], item[0]))
        ],
        edges=[edge_out(edge) for edge in traversed],
        truncated=truncated,
    )


@router.get("/impact", response_model=ImpactResult)
async def impact(
    project_id: str,
    artifact_id: str,
    depth: int = Query(default=3, ge=1, le=5),
    edge_type: list[str] = Query(default=["depends_on", "implements", "validated_by"]),
    user: str = Depends(session_user),
    db: AsyncSession = Depends(db_session),
) -> ImpactResult:
    await project_membership(db, project_id, user)
    records, edges = await load_project_graph(db, project_id)
    get_root(records, artifact_id)
    depths, _, truncated = traverse(
        records,
        edges,
        root_id=artifact_id,
        depth_limit=depth,
        direction="incoming",
        edge_types=set(edge_type),
    )
    return ImpactResult(
        root_id=artifact_id,
        max_depth=depth,
        affected=[
            GraphNode(artifact=as_contract(records[node_id]), depth=node_depth)
            for node_id, node_depth in sorted(depths.items(), key=lambda item: (item[1], item[0]))
            if node_id != artifact_id
        ],
        truncated=truncated,
    )


@router.get("/traceability", response_model=TraceabilityResult)
async def traceability(
    project_id: str,
    requirement_id: str,
    user: str = Depends(session_user),
    db: AsyncSession = Depends(db_session),
) -> TraceabilityResult:
    await project_membership(db, project_id, user)
    records, edges = await load_project_graph(db, project_id)
    requirement = get_root(records, requirement_id)
    if requirement.type != "requirement":
        raise HTTPException(status_code=422, detail="Traceability root must be a requirement")
    linked: dict[str, set[str]] = {
        "screen": set(),
        "component": set(),
        "api_endpoint": set(),
        "task": set(),
        "test_case": set(),
        "evaluation_case": set(),
    }
    for edge in edges:
        if edge.edge_type == "implements" and edge.target_id == requirement_id:
            record = records.get(edge.source_id)
            if record is not None and record.type in {
                "screen",
                "component",
                "api_endpoint",
                "task",
            }:
                linked[record.type].add(record.id)
        elif edge.edge_type == "validated_by" and edge.source_id == requirement_id:
            record = records.get(edge.target_id)
            if record is not None and record.type in {"test_case", "evaluation_case"}:
                linked[record.type].add(record.id)
    artifacts = {
        artifact_id: as_contract(records[artifact_id])
        for ids in linked.values()
        for artifact_id in ids
    }
    gaps = []
    if not any(linked[name] for name in ("screen", "component", "api_endpoint")):
        gaps.append("no implementation artifacts")
    if not any(linked[name] for name in ("test_case", "evaluation_case")):
        gaps.append("no validation artifacts")
    return TraceabilityResult(
        requirement=as_contract(requirement),
        screens=[artifacts[artifact_id] for artifact_id in sorted(linked["screen"])],
        components=[artifacts[artifact_id] for artifact_id in sorted(linked["component"])],
        apis=[artifacts[artifact_id] for artifact_id in sorted(linked["api_endpoint"])],
        tests=[
            artifacts[artifact_id]
            for artifact_id in sorted(linked["test_case"] | linked["evaluation_case"])
        ],
        tasks=[artifacts[artifact_id] for artifact_id in sorted(linked["task"])],
        gaps=gaps,
    )
