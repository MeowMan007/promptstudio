"""Add tenant-scoped artifacts and immutable revision snapshots."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0004_artifacts_revisions"
down_revision = "0003_project_alias_counters"
branch_labels = None
depends_on = None

json_type = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "artifacts",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column(
            "project_id",
            sa.Text(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("alias", sa.String(10), nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("schema_version", sa.String(32), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False, server_default=""),
        sa.Column("payload", json_type, nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="scratch"),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_by", sa.Text(), nullable=False),
        sa.Column("updated_by", sa.Text(), nullable=False),
        sa.Column("provenance", json_type, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("visibility", sa.String(16), nullable=False, server_default="project"),
        sa.Column("sensitivity", sa.String(24), nullable=False, server_default="internal"),
        sa.Column("locked_fields", json_type, nullable=False, server_default=sa.text("'[]'")),
        sa.Column("owner", sa.Text()),
        sa.Column("tags", postgresql.ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("archived_from_status", sa.String(16)),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("project_id", "alias", name="artifact_project_alias"),
        sa.CheckConstraint(
            "status IN ('scratch','proposed','in_review','approved','rejected',"
            "'deprecated','archived')",
            name="artifact_status",
        ),
        sa.CheckConstraint(
            "visibility IN ('project','private','restricted')", name="artifact_visibility"
        ),
        sa.CheckConstraint(
            "sensitivity IN ('public','internal','confidential','secret-bearing')",
            name="artifact_sensitivity",
        ),
    )
    op.create_index("ix_artifacts_project_id", "artifacts", ["project_id"])
    op.create_index("artifacts_type_status_idx", "artifacts", ["project_id", "type", "status"])
    op.create_index(
        "artifacts_payload_gin",
        "artifacts",
        ["payload"],
        postgresql_using="gin",
        postgresql_ops={"payload": "jsonb_path_ops"},
    )
    op.create_index(
        "artifacts_fts_idx",
        "artifacts",
        [sa.text("to_tsvector('english', title || ' ' || body)")],
        postgresql_using="gin",
    )
    op.create_table(
        "artifact_revisions",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column(
            "artifact_id",
            sa.Text(),
            sa.ForeignKey("artifacts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("snapshot", json_type, nullable=False),
        sa.Column("change_summary", sa.Text()),
        sa.Column("actor_id", sa.Text(), nullable=False),
        sa.Column("run_id", sa.Text()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("artifact_id", "revision", name="artifact_revision_number"),
    )
    op.create_index("ix_artifact_revisions_artifact_id", "artifact_revisions", ["artifact_id"])

    for table in ("artifacts", "artifact_revisions"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    op.execute("GRANT SELECT, INSERT, UPDATE ON artifacts TO prompt_studio_app")
    op.execute("GRANT SELECT, INSERT ON artifact_revisions TO prompt_studio_app")
    op.execute(
        """
        CREATE POLICY artifacts_select ON artifacts FOR SELECT
          USING (EXISTS (
            SELECT 1 FROM projects p
            WHERE p.id = project_id AND app_is_workspace_member(p.workspace_id)
          ))
        """
    )
    op.execute(
        """
        CREATE POLICY artifacts_insert ON artifacts FOR INSERT
          WITH CHECK (EXISTS (
            SELECT 1 FROM projects p
            WHERE p.id = project_id
              AND app_is_workspace_member(p.workspace_id, ARRAY['owner','editor'])
          ))
        """
    )
    op.execute(
        """
        CREATE POLICY artifacts_update ON artifacts FOR UPDATE
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
    op.execute(
        """
        CREATE POLICY artifact_revisions_select ON artifact_revisions FOR SELECT
          USING (EXISTS (
            SELECT 1 FROM artifacts a
            JOIN projects p ON p.id = a.project_id
            WHERE a.id = artifact_id AND app_is_workspace_member(p.workspace_id)
          ))
        """
    )
    op.execute(
        """
        CREATE POLICY artifact_revisions_insert ON artifact_revisions FOR INSERT
          WITH CHECK (
            actor_id = current_setting('app.user_id', true)
            AND EXISTS (
              SELECT 1 FROM artifacts a
              JOIN projects p ON p.id = a.project_id
              WHERE a.id = artifact_id
                AND app_is_workspace_member(p.workspace_id, ARRAY['owner','editor'])
            )
          )
        """
    )


def downgrade() -> None:
    for policy, table in (
        ("artifact_revisions_insert", "artifact_revisions"),
        ("artifact_revisions_select", "artifact_revisions"),
        ("artifacts_update", "artifacts"),
        ("artifacts_insert", "artifacts"),
        ("artifacts_select", "artifacts"),
    ):
        op.execute(f"DROP POLICY IF EXISTS {policy} ON {table}")
    op.execute("ALTER TABLE artifact_revisions NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE artifact_revisions DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE artifacts NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE artifacts DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_artifact_revisions_artifact_id", table_name="artifact_revisions")
    op.drop_table("artifact_revisions")
    op.drop_index("artifacts_fts_idx", table_name="artifacts")
    op.drop_index("artifacts_payload_gin", table_name="artifacts")
    op.drop_index("artifacts_type_status_idx", table_name="artifacts")
    op.drop_index("ix_artifacts_project_id", table_name="artifacts")
    op.drop_table("artifacts")
