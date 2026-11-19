from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.database_models import Base
from backend.app.identity.models import JSONDocument


class ProjectionRecord(Base):
    __tablename__ = "projection_records"
    __table_args__ = (
        UniqueConstraint("project_id", "id", name="projection_project_id_id"),
        ForeignKeyConstraint(
            ["project_id", "artifact_id"],
            ["artifacts.project_id", "artifacts.id"],
            ondelete="CASCADE",
            name="projection_artifact_same_project",
        ),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    view_id: Mapped[str] = mapped_column(Text, nullable=False)
    artifact_id: Mapped[str | None] = mapped_column(Text)
    engine: Mapped[str] = mapped_column(String(32), nullable=False)
    engine_element_ids: Mapped[list[str]] = mapped_column(
        JSONDocument, nullable=False, default=list, server_default="[]"
    )
    visual_type: Mapped[str] = mapped_column(String(32), nullable=False)
    position: Mapped[dict[str, Any]] = mapped_column(JSONDocument, nullable=False)
    style: Mapped[dict[str, Any]] = mapped_column(
        JSONDocument, nullable=False, default=dict, server_default="{}"
    )
    frame_settings: Mapped[dict[str, Any] | None] = mapped_column(JSONDocument)
    frame_id: Mapped[str | None] = mapped_column(Text)
    collapsed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    semantic_hash: Mapped[str | None] = mapped_column(String(71))
    layout_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    created_by: Mapped[str] = mapped_column(Text, nullable=False)
    updated_by: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class ProjectionLayoutOperation(Base):
    __tablename__ = "projection_layout_operations"
    __table_args__ = (UniqueConstraint("project_id", "id", name="layout_operation_project_id_id"),)

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    layout_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    operation_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    before_positions: Mapped[dict[str, Any]] = mapped_column(JSONDocument, nullable=False)
    after_positions: Mapped[dict[str, Any]] = mapped_column(JSONDocument, nullable=False)
    undone_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
