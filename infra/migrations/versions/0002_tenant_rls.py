"""Enforce workspace tenancy and roles with PostgreSQL row-level security."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002_tenant_rls"
down_revision = "0001_workspace_project"
branch_labels = None
depends_on = None

TABLES = (
    "workspaces",
    "workspace_members",
    "projects",
    "project_events",
    "audit_events",
)


def upgrade() -> None:
    op.execute(
        """
        DO $$ BEGIN
          IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'prompt_studio_app') THEN
            CREATE ROLE prompt_studio_app NOLOGIN NOBYPASSRLS;
          END IF;
          IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'prompt_studio_policy') THEN
            CREATE ROLE prompt_studio_policy NOLOGIN BYPASSRLS;
          END IF;
        END $$;
        """
    )
    bind = op.get_bind()
    migration_user = bind.execute(sa.text("SELECT current_user")).scalar_one()
    quoted_user = bind.dialect.identifier_preparer.quote(migration_user)
    op.execute(f"GRANT prompt_studio_app TO {quoted_user}")
    op.execute("GRANT SELECT ON workspace_members TO prompt_studio_policy")
    function_sql = """
        CREATE FUNCTION app_is_workspace_member(
          target_workspace_id text,
          allowed_roles text[] DEFAULT NULL
        )
        RETURNS boolean
        LANGUAGE sql
        STABLE
        SECURITY DEFINER
        SET search_path = public, pg_temp
        AS $$
          SELECT EXISTS (
            SELECT 1 FROM public.workspace_members wm
            WHERE wm.workspace_id = target_workspace_id
              AND wm.user_id = current_setting('app.user_id', true)
              AND wm.status = 'active'
              AND (allowed_roles IS NULL OR wm.role = ANY(allowed_roles))
          );
        $$
        """
    op.execute(function_sql)
    op.execute("ALTER FUNCTION app_is_workspace_member(text, text[]) OWNER TO prompt_studio_policy")
    op.execute(
        "GRANT EXECUTE ON FUNCTION app_is_workspace_member(text, text[]) TO prompt_studio_app"
    )
    op.execute("GRANT USAGE ON SCHEMA public TO prompt_studio_app, prompt_studio_policy")
    for table in TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON " + ", ".join(TABLES) + " TO prompt_studio_app"
    )

    policy_sql = """
        CREATE POLICY workspaces_select ON workspaces FOR SELECT
          USING (
            app_is_workspace_member(id)
            OR id = current_setting('app.workspace_create_id', true)
          );
        CREATE POLICY workspaces_insert ON workspaces FOR INSERT
          WITH CHECK (current_setting('app.user_id', true) IS NOT NULL);
        CREATE POLICY workspaces_update ON workspaces FOR UPDATE
          USING (app_is_workspace_member(id, ARRAY['owner']))
          WITH CHECK (app_is_workspace_member(id, ARRAY['owner']));

        CREATE POLICY members_select ON workspace_members FOR SELECT
          USING (app_is_workspace_member(workspace_id));
        CREATE POLICY members_insert ON workspace_members FOR INSERT
          WITH CHECK (
            (user_id = current_setting('app.user_id', true) AND role = 'owner')
            OR app_is_workspace_member(workspace_id, ARRAY['owner'])
          );
        CREATE POLICY members_update ON workspace_members FOR UPDATE
          USING (app_is_workspace_member(workspace_id, ARRAY['owner']))
          WITH CHECK (app_is_workspace_member(workspace_id, ARRAY['owner']));
        CREATE POLICY members_delete ON workspace_members FOR DELETE
          USING (app_is_workspace_member(workspace_id, ARRAY['owner']));

        CREATE POLICY projects_select ON projects FOR SELECT
          USING (app_is_workspace_member(workspace_id));
        CREATE POLICY projects_insert ON projects FOR INSERT
          WITH CHECK (app_is_workspace_member(workspace_id, ARRAY['owner','editor']));
        CREATE POLICY projects_update ON projects FOR UPDATE
          USING (app_is_workspace_member(workspace_id, ARRAY['owner','editor']))
          WITH CHECK (app_is_workspace_member(workspace_id, ARRAY['owner','editor']));
        CREATE POLICY projects_delete ON projects FOR DELETE
          USING (app_is_workspace_member(workspace_id, ARRAY['owner','editor']));

        CREATE POLICY project_events_select ON project_events FOR SELECT
          USING (EXISTS (
            SELECT 1 FROM projects p WHERE p.id = project_id
              AND app_is_workspace_member(p.workspace_id)
          ));
        CREATE POLICY project_events_insert ON project_events FOR INSERT
          WITH CHECK (actor_id = current_setting('app.user_id', true) AND EXISTS (
            SELECT 1 FROM projects p WHERE p.id = project_id
              AND app_is_workspace_member(p.workspace_id, ARRAY['owner','editor'])
          ));

        CREATE POLICY audit_events_select ON audit_events FOR SELECT
          USING (app_is_workspace_member(workspace_id));
        CREATE POLICY audit_events_insert ON audit_events FOR INSERT
          WITH CHECK (
            actor_id = current_setting('app.user_id', true)
            AND app_is_workspace_member(workspace_id)
          );
        """
    for statement in policy_sql.split(";"):
        if statement.strip():
            op.execute(statement)


def downgrade() -> None:
    for policy, table in (
        ("workspaces_select", "workspaces"),
        ("workspaces_insert", "workspaces"),
        ("workspaces_update", "workspaces"),
        ("members_select", "workspace_members"),
        ("members_insert", "workspace_members"),
        ("members_update", "workspace_members"),
        ("members_delete", "workspace_members"),
        ("projects_select", "projects"),
        ("projects_insert", "projects"),
        ("projects_update", "projects"),
        ("projects_delete", "projects"),
        ("project_events_select", "project_events"),
        ("project_events_insert", "project_events"),
        ("audit_events_select", "audit_events"),
        ("audit_events_insert", "audit_events"),
    ):
        op.execute(f"DROP POLICY IF EXISTS {policy} ON {table}")
    for table in TABLES:
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
    op.execute("DROP FUNCTION IF EXISTS app_is_workspace_member(text, text[])")
