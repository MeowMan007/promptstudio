"""Add transactional per-project artifact alias counters."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003_project_alias_counters"
down_revision = "0002_tenant_rls"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "project_alias_counters",
        sa.Column(
            "project_id",
            sa.Text(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("prefix", sa.String(3), nullable=False),
        sa.Column("next_value", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("project_id", "prefix"),
        sa.CheckConstraint("next_value BETWEEN 2 AND 1000000", name="alias_counter_range"),
    )
    op.execute("ALTER TABLE project_alias_counters ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE project_alias_counters FORCE ROW LEVEL SECURITY")
    op.execute("GRANT SELECT, INSERT, UPDATE ON project_alias_counters TO prompt_studio_app")
    member_policy = """
      EXISTS (
        SELECT 1 FROM projects p
        WHERE p.id = project_id
          AND app_is_workspace_member(p.workspace_id, ARRAY['owner','editor'])
      )
    """
    op.execute(
        "CREATE POLICY alias_counter_select ON project_alias_counters "
        f"FOR SELECT USING ({member_policy})"
    )
    op.execute(
        "CREATE POLICY alias_counter_insert ON project_alias_counters "
        f"FOR INSERT WITH CHECK ({member_policy})"
    )
    op.execute(
        "CREATE POLICY alias_counter_update ON project_alias_counters "
        f"FOR UPDATE USING ({member_policy}) WITH CHECK ({member_policy})"
    )


def downgrade() -> None:
    for policy in ("alias_counter_select", "alias_counter_insert", "alias_counter_update"):
        op.execute(f"DROP POLICY IF EXISTS {policy} ON project_alias_counters")
    op.drop_table("project_alias_counters")
