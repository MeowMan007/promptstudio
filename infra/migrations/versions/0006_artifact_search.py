"""Add full-text and trigram indexes for artifact search."""

from __future__ import annotations

from alembic import op

revision = "0006_artifact_search"
down_revision = "0005_artifact_edges"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute(
        """
        ALTER TABLE artifacts ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (
          to_tsvector(
            'english'::regconfig,
            coalesce(title, '') || ' ' || coalesce(body, '') || ' ' || coalesce(payload::text, '')
          )
        ) STORED
        """
    )
    op.execute("CREATE INDEX artifacts_search_vector_idx ON artifacts USING gin (search_vector)")
    op.execute("CREATE INDEX artifacts_title_trgm_idx ON artifacts USING gin (title gin_trgm_ops)")
    op.create_index(
        "artifacts_project_type_status_cursor_idx",
        "artifacts",
        ["project_id", "type", "status", "created_at", "id"],
    )
    op.create_index("artifacts_project_type_idx", "artifacts", ["project_id", "type"])
    op.create_index("artifacts_project_status_idx", "artifacts", ["project_id", "status"])


def downgrade() -> None:
    op.drop_index("artifacts_project_status_idx", table_name="artifacts")
    op.drop_index("artifacts_project_type_idx", table_name="artifacts")
    op.drop_index("artifacts_project_type_status_cursor_idx", table_name="artifacts")
    op.execute("DROP INDEX artifacts_title_trgm_idx")
    op.execute("DROP INDEX artifacts_search_vector_idx")
    op.drop_column("artifacts", "search_vector")
