from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.database_models import Base
from backend.app.identity.models import JSONDocument


class ArtifactEdge(Base):
    __tablename__ = "artifact_edges"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "source_id", "target_id", "edge_type", name="edge_project_pair_type"
        ),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_id: Mapped[str] = mapped_column(
        ForeignKey("artifacts.id", ondelete="CASCADE"), nullable=False
    )
    target_id: Mapped[str] = mapped_column(
        ForeignKey("artifacts.id", ondelete="CASCADE"), nullable=False
    )
    edge_type: Mapped[str] = mapped_column(Text, nullable=False)
    edge_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONDocument, nullable=False, default=dict, server_default="{}"
    )
    created_by: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
