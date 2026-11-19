"""Add tenant-scoped typed artifact edges."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0005_artifact_edges"
down_revision = "0004_artifacts_revisions"
branch_labels = None
depends_on = None

json_type = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.create_unique_constraint("artifact_project_id_id", "artifacts", ["project_id", "id"])
    op.create_table(
        "artifact_edges",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("project_id", sa.Text(), nullable=False),
        sa.Column("source_id", sa.Text(), nullable=False),
        sa.Column("target_id", sa.Text(), nullable=False),
        sa.Column("edge_type", sa.Text(), nullable=False),
        sa.Column("metadata", json_type, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_by", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["project_id", "source_id"],
            ["artifacts.project_id", "artifacts.id"],
            ondelete="CASCADE",
            name="edge_source_same_project",
        ),
        sa.ForeignKeyConstraint(
            ["project_id", "target_id"],
            ["artifacts.project_id", "artifacts.id"],
            ondelete="CASCADE",
            name="edge_target_same_project",
        ),
        sa.UniqueConstraint(
            "project_id", "source_id", "target_id", "edge_type", name="edge_project_pair_type"
        ),
    )
    op.create_index("ix_artifact_edges_project_id", "artifact_edges", ["project_id"])
    op.create_index("edges_source_idx", "artifact_edges", ["project_id", "source_id", "edge_type"])
    op.create_index("edges_target_idx", "artifact_edges", ["project_id", "target_id", "edge_type"])
    op.execute("ALTER TABLE artifact_edges ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE artifact_edges FORCE ROW LEVEL SECURITY")
    op.execute("GRANT SELECT, INSERT, DELETE ON artifact_edges TO prompt_studio_app")
    op.execute(
        """
        CREATE POLICY edges_select ON artifact_edges FOR SELECT
          USING (EXISTS (
            SELECT 1 FROM projects p
            WHERE p.id = project_id AND app_is_workspace_member(p.workspace_id)
          ))
        """
    )
    op.execute(
        """
        CREATE POLICY edges_insert ON artifact_edges FOR INSERT
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
        CREATE POLICY edges_delete ON artifact_edges FOR DELETE
          USING (EXISTS (
            SELECT 1 FROM projects p
            WHERE p.id = project_id
              AND app_is_workspace_member(p.workspace_id, ARRAY['owner','editor'])
          ))
        """
    )


def downgrade() -> None:
    for policy in ("edges_select", "edges_insert", "edges_delete"):
        op.execute(f"DROP POLICY IF EXISTS {policy} ON artifact_edges")
    op.execute("ALTER TABLE artifact_edges NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE artifact_edges DISABLE ROW LEVEL SECURITY")
    op.drop_index("edges_target_idx", table_name="artifact_edges")
    op.drop_index("edges_source_idx", table_name="artifact_edges")
    op.drop_index("ix_artifact_edges_project_id", table_name="artifact_edges")
    op.drop_table("artifact_edges")
    op.drop_constraint("artifact_project_id_id", "artifacts", type_="unique")
