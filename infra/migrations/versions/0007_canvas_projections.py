"""Persist canvas projections and independent layout revisions."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0007_canvas_projections"
down_revision = "0006_artifact_search"
branch_labels = None
depends_on = None

json_type = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column("layout_revision", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_table(
        "projection_records",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("project_id", sa.Text(), nullable=False),
        sa.Column("view_id", sa.Text(), nullable=False),
        sa.Column("artifact_id", sa.Text()),
        sa.Column("engine", sa.String(32), nullable=False),
        sa.Column("engine_element_ids", json_type, nullable=False, server_default=sa.text("'[]'")),
        sa.Column("visual_type", sa.String(32), nullable=False),
        sa.Column("position", json_type, nullable=False),
        sa.Column("style", json_type, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("frame_id", sa.Text()),
        sa.Column("collapsed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("locked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("semantic_hash", sa.String(71)),
        sa.Column("layout_revision", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Text(), nullable=False),
        sa.Column("updated_by", sa.Text(), nullable=False),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["project_id", "artifact_id"],
            ["artifacts.project_id", "artifacts.id"],
            ondelete="CASCADE",
            name="projection_artifact_same_project",
        ),
        sa.UniqueConstraint("project_id", "id", name="projection_project_id_id"),
        sa.CheckConstraint("layout_revision >= 0", name="projection_layout_revision_positive"),
    )
    op.create_index("projection_project_view_idx", "projection_records", ["project_id", "view_id"])
    op.create_index("projection_artifact_idx", "projection_records", ["project_id", "artifact_id"])
    op.execute("ALTER TABLE projection_records ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE projection_records FORCE ROW LEVEL SECURITY")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON projection_records TO prompt_studio_app")
    op.execute(
        """
        CREATE POLICY projections_select ON projection_records FOR SELECT
          USING (EXISTS (
            SELECT 1 FROM projects p
            WHERE p.id = project_id AND app_is_workspace_member(p.workspace_id)
          ))
        """
    )
    op.execute(
        """
        CREATE POLICY projections_insert ON projection_records FOR INSERT
          WITH CHECK (
            created_by = current_setting('app.user_id', true)
            AND updated_by = current_setting('app.user_id', true)
            AND EXISTS (
              SELECT 1 FROM projects p
              WHERE p.id = project_id
                AND app_is_workspace_member(p.workspace_id, ARRAY['owner','editor'])
            )
          )
        """
    )
    op.execute(
        """
        CREATE POLICY projections_update ON projection_records FOR UPDATE
          USING (EXISTS (
            SELECT 1 FROM projects p
            WHERE p.id = project_id
              AND app_is_workspace_member(p.workspace_id, ARRAY['owner','editor'])
          ))
          WITH CHECK (
            updated_by = current_setting('app.user_id', true)
            AND EXISTS (
              SELECT 1 FROM projects p
              WHERE p.id = project_id
                AND app_is_workspace_member(p.workspace_id, ARRAY['owner','editor'])
            )
          )
        """
    )
    op.execute(
        """
        CREATE POLICY projections_delete ON projection_records FOR DELETE
          USING (EXISTS (
            SELECT 1 FROM projects p
            WHERE p.id = project_id
              AND app_is_workspace_member(p.workspace_id, ARRAY['owner','editor'])
          ))
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE projection_records")
    op.drop_column("projects", "layout_revision")
