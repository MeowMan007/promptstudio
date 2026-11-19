from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    ARRAY,
    CheckConstraint,
    Computed,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database_models import Base
from backend.app.identity.models import JSONDocument


class ArtifactRecord(Base):
    __tablename__ = "artifacts"
    __table_args__ = (
        UniqueConstraint("project_id", "alias", name="artifact_project_alias"),
        CheckConstraint(
            "status IN ('scratch','proposed','in_review','approved','rejected',"
            "'deprecated','archived')",
            name="artifact_status",
        ),
        CheckConstraint(
            "visibility IN ('project','private','restricted')", name="artifact_visibility"
        ),
        CheckConstraint(
            "sensitivity IN ('public','internal','confidential','secret-bearing')",
            name="artifact_sensitivity",
        ),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    alias: Mapped[str] = mapped_column(String(10), nullable=False)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    schema_version: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    payload: Mapped[dict[str, Any]] = mapped_column(JSONDocument, nullable=False)
    search_vector: Mapped[str] = mapped_column(
        TSVECTOR,
        Computed(
            "to_tsvector('english'::regconfig, "
            "coalesce(title, '') || ' ' || coalesce(body, '') || ' ' "
            "|| coalesce(payload::text, ''))",
            persisted=True,
        ),
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="scratch")
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_by: Mapped[str] = mapped_column(Text, nullable=False)
    updated_by: Mapped[str] = mapped_column(Text, nullable=False)
    provenance: Mapped[dict[str, Any]] = mapped_column(
        JSONDocument, nullable=False, default=dict, server_default="{}"
    )
    visibility: Mapped[str] = mapped_column(
        String(16), nullable=False, default="project", server_default="project"
    )
    sensitivity: Mapped[str] = mapped_column(
        String(24), nullable=False, default="internal", server_default="internal"
    )
    locked_fields: Mapped[list[str]] = mapped_column(
        JSONDocument, nullable=False, default=list, server_default="[]"
    )
    owner: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, default=list, server_default="{}"
    )
    archived_from_status: Mapped[str | None] = mapped_column(String(16))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    revisions: Mapped[list[ArtifactRevisionRecord]] = relationship(
        back_populates="artifact", cascade="all, delete-orphan"
    )


class ArtifactRevisionRecord(Base):
    __tablename__ = "artifact_revisions"
    __table_args__ = (UniqueConstraint("artifact_id", "revision", name="artifact_revision_number"),)

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    artifact_id: Mapped[str] = mapped_column(
        ForeignKey("artifacts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSONDocument, nullable=False)
    change_summary: Mapped[str | None] = mapped_column(Text)
    actor_id: Mapped[str] = mapped_column(Text, nullable=False)
    run_id: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    artifact: Mapped[ArtifactRecord] = relationship(back_populates="revisions")
