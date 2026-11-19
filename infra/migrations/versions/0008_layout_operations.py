"""Add frame metadata and atomic layout operation history."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0008_layout_operations"
down_revision = "0007_canvas_projections"
branch_labels = None
depends_on = None

json_type = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.add_column("projection_records", sa.Column("frame_settings", json_type))
    op.create_table(
        "projection_layout_operations",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("project_id", sa.Text(), nullable=False),
        sa.Column("layout_revision", sa.Integer(), nullable=False),
        sa.Column("operation_kind", sa.String(32), nullable=False),
        sa.Column("before_positions", json_type, nullable=False),
        sa.Column("after_positions", json_type, nullable=False),
        sa.Column("undone_at", sa.DateTime(timezone=True)),
        sa.Column("created_by", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("project_id", "id", name="layout_operation_project_id_id"),
        sa.CheckConstraint("layout_revision >= 0", name="layout_operation_revision_positive"),
    )
    op.create_index(
        "layout_operations_project_revision_idx",
        "projection_layout_operations",
        ["project_id", "layout_revision"],
    )
    op.execute("ALTER TABLE projection_layout_operations ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE projection_layout_operations FORCE ROW LEVEL SECURITY")
    op.execute("GRANT SELECT, INSERT, UPDATE ON projection_layout_operations TO prompt_studio_app")
    op.execute(
        """
        CREATE POLICY layout_operations_select ON projection_layout_operations FOR SELECT
          USING (EXISTS (
            SELECT 1 FROM projects p
            WHERE p.id = project_id AND app_is_workspace_member(p.workspace_id)
          ))
        """
    )
    op.execute(
        """
        CREATE POLICY layout_operations_insert ON projection_layout_operations FOR INSERT
          WITH CHECK (
            created_by = current_setting('app.user_id', true)
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
        CREATE POLICY layout_operations_update ON projection_layout_operations FOR UPDATE
          USING (EXISTS (
            SELECT 1 FROM projects p
            WHERE p.id = project_id
              AND app_is_workspace_member(p.workspace_id, ARRAY['owner','editor'])
          ))
          WITH CHECK (EXISTS (
            SELECT 1 FROM projects p
            WHERE p.id = project_id
              AND app_is_workspace_member(p.workspace_id, ARRAY['owner','editor'])
          ))
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE projection_layout_operations")
    op.drop_column("projection_records", "frame_settings")
