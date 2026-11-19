from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient
from prompt_studio_api.identity.oidc import AuthSettings, create_oidc_client
from prompt_studio_api.main import create_app
from starlette.responses import RedirectResponse


class FakeOIDCClient:
    def __init__(self, userinfo: dict[str, Any] | None = None) -> None:
        self.userinfo = userinfo or {
            "sub": "user-123",
            "email": "user@example.test",
            "name": "Test User",
        }

    async def authorize_redirect(self, request: Any, redirect_uri: str) -> RedirectResponse:
        assert redirect_uri == "https://studio.example.test/auth/callback"
        return RedirectResponse("https://identity.example.test/authorize", status_code=302)

    async def authorize_access_token(self, request: Any) -> dict[str, Any]:
        return {"userinfo": self.userinfo}


def settings(
    *, issuer: str | None = "https://identity.example.test", ttl: int = 60
) -> AuthSettings:
    return AuthSettings(
        issuer=issuer,
        client_id="client-id" if issuer else None,
        client_secret="client-secret" if issuer else None,
        redirect_uri="https://studio.example.test/auth/callback" if issuer else None,
        session_secret_key="test-session-secret-that-is-long-enough-for-itsdangerous",
        session_ttl_seconds=ttl,
        session_cookie_secure=False,
    )


def test_authlib_client_is_configured_for_openid_connect() -> None:
    client = create_oidc_client(settings())

    assert client is not None
    assert client.client_id == "client-id"
    assert client.client_kwargs["scope"] == "openid profile email"


def test_oidc_login_creates_session_and_logout_clears_it() -> None:
    app = create_app(settings())
    app.state.oidc_client = FakeOIDCClient()

    with TestClient(app) as client:
        login = client.get("/auth/login", follow_redirects=False)
        assert login.status_code == 302
        assert login.headers["location"] == "https://identity.example.test/authorize"

        callback = client.get("/auth/callback", follow_redirects=False)
        assert callback.status_code == 303
        assert "prompt_studio_session=" in callback.headers["set-cookie"]
        assert "httponly" in callback.headers["set-cookie"].lower()
        assert "samesite=lax" in callback.headers["set-cookie"].lower()

        current = client.get("/auth/me")
        assert current.status_code == 200
        assert current.json()["user"] == {"sub": "user-123"}

        logout = client.post("/auth/logout")
        assert logout.status_code == 204
        assert client.get("/auth/me").status_code == 401


def test_session_expiry_is_enforced_on_api_requests() -> None:
    now = [1_000.0]
    app = create_app(settings(ttl=60))
    app.state.clock = lambda: now[0]
    app.state.oidc_client = FakeOIDCClient()

    with TestClient(app) as client:
        assert client.get("/auth/callback", follow_redirects=False).status_code == 303
        now[0] = 1_060.0
        assert client.get("/auth/me").status_code == 401


def test_oidc_routes_reject_missing_configuration_and_missing_subject() -> None:
    unconfigured = create_app(settings(issuer=None))
    with TestClient(unconfigured) as client:
        assert client.get("/auth/login").status_code == 503

    app = create_app(settings())
    app.state.oidc_client = FakeOIDCClient({"email": "no-sub@example.test"})
    with TestClient(app) as client:
        assert client.get("/auth/callback").status_code == 401


def test_api_errors_use_envelope_and_correlation_id(caplog: Any) -> None:
    import logging
    import os

    caplog.set_level(logging.INFO, logger="prompt_studio.api")
    app = create_app(settings(), database_url=os.environ["DATABASE_URL"])
    app.state.oidc_client = FakeOIDCClient()

    @app.get("/test-unhandled-error")
    async def unhandled_error() -> None:
        raise RuntimeError("sensitive internal detail")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/api/v1/workspaces", headers={"X-Correlation-ID": "corr-test-123"})
        assert response.status_code == 401
        assert response.headers["x-correlation-id"] == "corr-test-123"
        assert response.json() == {
            "error": {
                "code": "auth.required",
                "message": "Authentication required",
                "details": {},
                "correlation_id": "corr-test-123",
                "retryable": False,
            }
        }

        client.get("/auth/callback", follow_redirects=False)
        invalid = client.post(
            "/api/v1/workspaces",
            json={"name": ""},
            headers={"X-Correlation-ID": "corr-validation"},
        )
        assert invalid.status_code == 422
        assert invalid.json()["error"]["code"] == "request.validation"
        assert invalid.json()["error"]["correlation_id"] == "corr-validation"
        assert invalid.headers["x-correlation-id"] == "corr-validation"

        missing = client.get("/api/v1/workspaces/not-a-real-id")
        assert missing.status_code == 404
        assert missing.json()["error"]["code"] == "resource.not_found"
        internal = client.get(
            "/test-unhandled-error", headers={"X-Correlation-ID": "corr-internal"}
        )
        assert internal.status_code == 500
        assert internal.headers["x-correlation-id"] == "corr-internal"
        assert internal.json()["error"]["code"] == "internal.error"
        assert "sensitive internal detail" not in internal.text
        assert any(
            "api.request" in record.getMessage() and "corr-test-123" in record.getMessage()
            for record in caplog.records
        )


def test_workspace_project_roles_and_tenant_isolation() -> None:
    import asyncio
    import os
    import secrets

    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    suffix = secrets.token_hex(4)
    app = create_app(settings(), database_url=os.environ["DATABASE_URL"])
    fake_oidc = FakeOIDCClient()
    app.state.oidc_client = fake_oidc
    with TestClient(app) as client:

        def login_as(user_id: str) -> str:
            fake_oidc.userinfo = {"sub": user_id}
            client.cookies.clear()
            assert client.get("/auth/callback", follow_redirects=False).status_code == 303
            return client.cookies.get("prompt_studio_session")

        def use_session(cookie: str) -> None:
            client.cookies.clear()
            client.cookies.set("prompt_studio_session", cookie)

        owner_id = f"owner-{suffix}"
        editor_id = f"editor-{suffix}"
        reviewer_id = f"reviewer-{suffix}"
        viewer_id = f"viewer-{suffix}"
        owner = login_as(owner_id)
        editor = login_as(editor_id)
        reviewer = login_as(reviewer_id)
        viewer = login_as(viewer_id)
        outsider = login_as(f"outsider-{suffix}")

        use_session(owner)
        workspace_response = client.post("/api/v1/workspaces", json={"name": "Role test"})
        assert workspace_response.status_code == 201, workspace_response.text
        workspace_id = workspace_response.json()["id"]
        assert client.get(f"/api/v1/workspaces/{workspace_id}").status_code == 200
        assert (
            client.delete(f"/api/v1/workspaces/{workspace_id}/members/{owner_id}").status_code
            == 409
        )

        for user_id, role in (
            (editor_id, "editor"),
            (reviewer_id, "reviewer"),
            (viewer_id, "viewer"),
        ):
            use_session(owner)
            added = client.post(
                f"/api/v1/workspaces/{workspace_id}/members",
                json={"user_id": user_id, "role": role},
            )
            assert added.status_code == 201, added.text

        use_session(outsider)
        assert client.get(f"/api/v1/workspaces/{workspace_id}/projects").status_code == 404
        use_session(editor)
        project_response = client.post(
            f"/api/v1/workspaces/{workspace_id}/projects", json={"name": "Editor project"}
        )
        assert project_response.status_code == 201, project_response.text
        project_id = project_response.json()["id"]
        assert project_response.json()["current_revision"] == 1

        use_session(reviewer)
        assert (
            client.patch(f"/api/v1/projects/{project_id}", json={"name": "Nope"}).status_code == 403
        )
        assert client.get(f"/api/v1/projects/{project_id}").status_code == 200
        use_session(viewer)
        assert client.get(f"/api/v1/workspaces/{workspace_id}").status_code == 200
        assert (
            client.post(
                f"/api/v1/workspaces/{workspace_id}/projects", json={"name": "Nope"}
            ).status_code
            == 403
        )
        use_session(outsider)
        assert client.get(f"/api/v1/projects/{project_id}").status_code == 404

        use_session(editor)
        updated = client.patch(f"/api/v1/projects/{project_id}", json={"name": "Revised"})
        assert updated.status_code == 200, updated.text
        assert updated.json()["current_revision"] == 2
        use_session(owner)
        assert client.delete(f"/api/v1/projects/{project_id}").status_code == 204
        assert client.get(f"/api/v1/projects/{project_id}").status_code == 404
        assert (
            client.delete(f"/api/v1/workspaces/{workspace_id}/members/{viewer_id}").status_code
            == 204
        )
        use_session(viewer)
        assert client.get(f"/api/v1/workspaces/{workspace_id}").status_code == 404

    async def database_read_as(user_id: str, requested_project_id: str) -> str | None:
        engine = create_async_engine(os.environ["DATABASE_URL"])
        try:
            async with engine.connect() as connection:
                async with connection.begin():
                    await connection.execute(text("SET LOCAL ROLE prompt_studio_app"))
                    await connection.execute(
                        text("SELECT set_config('app.user_id', :user_id, true)"),
                        {"user_id": user_id},
                    )
                    result = await connection.execute(
                        text("SELECT id FROM projects WHERE id = :project_id"),
                        {"project_id": project_id},
                    )
                    return result.scalar_one_or_none()
        finally:
            await engine.dispose()

    assert asyncio.run(database_read_as(f"outsider-{suffix}", project_id)) is None


def test_alias_allocation_is_unique_and_transactional_under_concurrency() -> None:
    import asyncio
    import os
    import secrets

    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from backend.app.ids import allocate_artifact_identity

    user_id = f"alias-owner-{secrets.token_hex(4)}"
    app = create_app(settings(), database_url=os.environ["DATABASE_URL"])
    app.state.oidc_client = FakeOIDCClient({"sub": user_id})
    with TestClient(app) as client:
        client.get("/auth/callback", follow_redirects=False)
        workspace = client.post("/api/v1/workspaces", json={"name": "Alias counter"})
        assert workspace.status_code == 201, workspace.text
        project = client.post(
            f"/api/v1/workspaces/{workspace.json()['id']}/projects",
            json={"name": "Counter project"},
        )
        assert project.status_code == 201, project.text
        project_id = project.json()["id"]

    async def allocate_concurrently() -> list[tuple[str, str]]:
        engine = create_async_engine(os.environ["DATABASE_URL"])
        sessions = async_sessionmaker(engine, expire_on_commit=False)

        async def allocate_one() -> tuple[str, str]:
            async with sessions() as session, session.begin():
                await session.execute(text("SET LOCAL ROLE prompt_studio_app"))
                await session.execute(
                    text("SELECT set_config('app.user_id', :user_id, true)"),
                    {"user_id": user_id},
                )
                return await allocate_artifact_identity(
                    session, project_id=project_id, artifact_type="requirement"
                )

        try:
            return list(await asyncio.gather(*(allocate_one() for _ in range(24))))
        finally:
            await engine.dispose()

    identities = asyncio.run(allocate_concurrently())
    artifact_ids, aliases = zip(*identities, strict=True)
    assert len(set(artifact_ids)) == 24
    assert len(set(aliases)) == 24
    assert set(aliases) == {f"REQ-{number:03d}" for number in range(1, 25)}


def test_artifact_revisions_events_validation_and_restore() -> None:
    import asyncio
    import os
    import secrets

    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    user_id = f"artifact-owner-{secrets.token_hex(4)}"
    app = create_app(settings(), database_url=os.environ["DATABASE_URL"])
    app.state.oidc_client = FakeOIDCClient({"sub": user_id})
    with TestClient(app) as client:
        client.get("/auth/callback", follow_redirects=False)
        workspace = client.post("/api/v1/workspaces", json={"name": "Artifact test"})
        assert workspace.status_code == 201, workspace.text
        project = client.post(
            f"/api/v1/workspaces/{workspace.json()['id']}/projects",
            json={"name": "Artifact project"},
        )
        assert project.status_code == 201, project.text
        project_id = project.json()["id"]

        create = client.post(
            f"/api/v1/projects/{project_id}/artifacts",
            json={
                "type": "requirement",
                "title": "A test requirement",
                "payload": {
                    "ears_pattern": "ubiquitous",
                    "clauses": {"response": "The system saves the requirement."},
                    "priority": "must",
                    "acceptance_criteria": [],
                },
            },
        )
        assert create.status_code == 201, create.text
        artifact = create.json()
        artifact_id = artifact["id"]
        assert artifact["alias"] == "REQ-001"
        assert artifact["revision"] == 1
        assert artifact["created_by"] == user_id

        searched = client.get(
            f"/api/v1/projects/{project_id}/artifacts",
            params={"q": "requirement", "type": "requirement", "status": "scratch"},
        )
        assert searched.status_code == 200, searched.text
        assert [item["id"] for item in searched.json()["items"]] == [artifact["id"]]

        updated = client.patch(
            f"/api/v1/artifacts/{artifact_id}",
            json={"base_revision": 1, "reason": "Clarified title", "title": "Updated requirement"},
        )
        assert updated.status_code == 200, updated.text
        assert updated.json()["revision"] == 2

        stale = client.patch(
            f"/api/v1/artifacts/{artifact_id}",
            json={"base_revision": 1, "reason": "Stale attempt", "title": "Old edit"},
        )
        assert stale.status_code == 409
        assert stale.json()["error"]["code"] == "conflict.stale_revision"

        invalid = client.patch(
            f"/api/v1/artifacts/{artifact_id}",
            json={
                "base_revision": 2,
                "reason": "Invalid payload test",
                "payload": {"ears_pattern": "unknown"},
            },
        )
        assert invalid.status_code == 422
        assert invalid.json()["error"]["code"] == "artifact.validation"
        assert client.get(f"/api/v1/artifacts/{artifact_id}").json()["revision"] == 2

        for base_revision, status in ((2, "proposed"), (3, "in_review"), (4, "approved")):
            transitioned = client.patch(
                f"/api/v1/artifacts/{artifact_id}",
                json={
                    "base_revision": base_revision,
                    "reason": "Advance lifecycle",
                    "status": status,
                },
            )
            assert transitioned.status_code == 200, transitioned.text
            assert transitioned.json()["revision"] == base_revision + 1

        archived = client.delete(
            f"/api/v1/artifacts/{artifact_id}",
            params={"base_revision": 5, "reason": "Archive completed artifact"},
        )
        assert archived.status_code == 200, archived.text
        assert archived.json()["status"] == "archived"
        assert client.get(f"/api/v1/artifacts/{artifact_id}").status_code == 404

        restored = client.post(
            f"/api/v1/artifacts/{artifact_id}/restore",
            json={"base_revision": 6, "reason": "Restore for follow-up"},
        )
        assert restored.status_code == 200, restored.text
        assert restored.json()["status"] == "approved"
        assert restored.json()["revision"] == 7

        revisions = client.get(f"/api/v1/artifacts/{artifact_id}/revisions")
        assert revisions.status_code == 200, revisions.text
        assert [item["revision"] for item in revisions.json()] == list(range(1, 8))

        diff = client.get(
            f"/api/v1/artifacts/{artifact_id}/diff",
            params={"from_revision": 1, "to_revision": 2},
        )
        assert diff.status_code == 200, diff.text
        assert any(
            change["path"] == "title"
            and change["before"] == "A test requirement"
            and change["after"] == "Updated requirement"
            for change in diff.json()["changes"]
        )

        restored_revision = client.post(
            f"/api/v1/artifacts/{artifact_id}/revisions/1/restore",
            params={"base_revision": 7, "reason": "Restore original draft"},
        )
        assert restored_revision.status_code == 200, restored_revision.text
        assert restored_revision.json()["revision"] == 8
        assert restored_revision.json()["title"] == "A test requirement"
        assert restored_revision.json()["status"] == "scratch"

        revisions = client.get(f"/api/v1/artifacts/{artifact_id}/revisions")
        assert [item["revision"] for item in revisions.json()] == list(range(1, 9))

    async def persistent_event_counts() -> tuple[int, int, int]:
        engine = create_async_engine(os.environ["DATABASE_URL"])
        try:
            async with engine.connect() as connection, connection.begin():
                await connection.execute(text("SET LOCAL ROLE prompt_studio_app"))
                await connection.execute(
                    text("SELECT set_config('app.user_id', :user_id, true)"),
                    {"user_id": user_id},
                )
                project_events = await connection.scalar(
                    text("SELECT count(*) FROM project_events WHERE project_id = :project_id"),
                    {"project_id": project_id},
                )
                audit_events = await connection.scalar(
                    text(
                        "SELECT count(*) FROM audit_events WHERE resource_type = 'artifact' "
                        "AND resource_id = :artifact_id"
                    ),
                    {"artifact_id": artifact_id},
                )
                project_revision = await connection.scalar(
                    text("SELECT current_revision FROM projects WHERE id = :project_id"),
                    {"project_id": project_id},
                )
                return int(project_events or 0), int(audit_events or 0), int(project_revision or 0)
        finally:
            await engine.dispose()

    assert asyncio.run(persistent_event_counts()) == (9, 8, 9)


def test_projection_layout_revision_is_independent_from_semantic_revision() -> None:
    import os
    import secrets

    user_id = f"projection-owner-{secrets.token_hex(4)}"
    app = create_app(settings(), database_url=os.environ["DATABASE_URL"])
    app.state.oidc_client = FakeOIDCClient({"sub": user_id})
    with TestClient(app) as client:
        client.get("/auth/callback", follow_redirects=False)
        workspace = client.post("/api/v1/workspaces", json={"name": "Projection test"})
        project = client.post(
            f"/api/v1/workspaces/{workspace.json()['id']}/projects",
            json={"name": "Canvas project"},
        )
        project_id = project.json()["id"]
        artifact_response = client.post(
            f"/api/v1/projects/{project_id}/artifacts",
            json={
                "type": "idea",
                "title": "Project the payment workflow",
                "payload": {"content": "A visible payment workflow card."},
            },
        )
        assert artifact_response.status_code == 201, artifact_response.text
        artifact = artifact_response.json()
        semantic_revision = project.json()["current_revision"] + 1
        projection_response = client.post(
            f"/api/v1/projects/{project_id}/projections",
            json={
                "view_id": "main",
                "artifact_id": artifact["id"],
                "engine_element_ids": ["card-1", "title-1"],
                "visual_type": "typed_card",
                "position": {"x": 40, "y": 60, "w": 320, "h": 180, "z": 1},
                "style": {"fill": "#ffffff"},
            },
        )
        assert projection_response.status_code == 201, projection_response.text
        projection = projection_response.json()
        assert projection["semantic_hash"].startswith("sha256:")
        assert projection["layout_revision"] == 1
        assert (
            client.get(f"/api/v1/workspaces/{workspace.json()['id']}/projects").json()[0][
                "current_revision"
            ]
            == semantic_revision
        )

        updated_response = client.patch(
            f"/api/v1/projects/{project_id}/projections/{projection['id']}",
            json={
                "base_layout_revision": 1,
                "position": {"x": 140, "y": 160, "w": 320, "h": 180, "z": 2},
            },
        )
        assert updated_response.status_code == 200, updated_response.text
        updated = updated_response.json()
        assert updated["position"]["x"] == 140
        assert updated["layout_revision"] == 2
        assert updated["semantic_hash"] == projection["semantic_hash"]
        project_after_move = client.get(
            f"/api/v1/workspaces/{workspace.json()['id']}/projects"
        ).json()[0]
        assert project_after_move["current_revision"] == semantic_revision
        assert project_after_move["layout_revision"] == 2
        assert client.get(f"/api/v1/artifacts/{artifact['id']}").json()["revision"] == 1

        stale = client.patch(
            f"/api/v1/projects/{project_id}/projections/{projection['id']}",
            json={
                "base_layout_revision": 1,
                "position": {"x": 0, "y": 0, "w": 100, "h": 100, "z": 0},
            },
        )
        assert stale.status_code == 409
        assert stale.json()["error"]["code"] == "conflict.stale_layout_revision"

        zones = client.get(f"/api/v1/projects/{project_id}/projections/default-zones")
        assert zones.status_code == 200, zones.text
        assert len(zones.json()) == 9
        second_projection = client.post(
            f"/api/v1/projects/{project_id}/projections",
            json={
                "view_id": "main",
                "artifact_id": artifact["id"],
                "visual_type": "typed_card",
                "position": {"x": 500, "y": 200, "w": 320, "h": 180, "z": 1},
            },
        )
        assert second_projection.status_code == 201, second_projection.text
        frame_response = client.post(
            f"/api/v1/projects/{project_id}/projections",
            json={
                "view_id": "main",
                "visual_type": "frame",
                "position": {"x": 0, "y": 0, "w": 900, "h": 640, "z": 0},
                "frame_settings": {
                    "title": "Requirements",
                    "order": 2,
                    "stage_binding": "S2_define",
                    "scope_filter": ["requirement"],
                    "auto_layout_policy": "grid",
                },
            },
        )
        assert frame_response.status_code == 201, frame_response.text
        assert frame_response.json()["frame_settings"]["title"] == "Requirements"

        auto_layout = client.post(
            f"/api/v1/projects/{project_id}/projections/auto-layout",
            json={
                "base_layout_revision": 4,
                "projection_ids": [projection["id"], second_projection.json()["id"]],
                "policy": "grid",
                "gap": 32,
                "snap_to_grid": True,
            },
        )
        assert auto_layout.status_code == 200, auto_layout.text
        assert auto_layout.json()["layout_revision"] == 5
        assert {position["x"] for position in auto_layout.json()["positions"].values()} == {0, 352}
        operation_id = auto_layout.json()["operation_id"]
        undone = client.post(
            f"/api/v1/projects/{project_id}/projections/layout-operations/{operation_id}/undo",
            json={"base_layout_revision": 5},
        )
        assert undone.status_code == 200, undone.text
        assert undone.json()["layout_revision"] == 6
        assert undone.json()["positions"][projection["id"]]["x"] == 140
        assert undone.json()["positions"][second_projection.json()["id"]]["x"] == 500
        assert (
            client.get(f"/api/v1/workspaces/{workspace.json()['id']}/projects").json()[0][
                "current_revision"
            ]
            == semantic_revision
        )

        valid_report = client.get(f"/api/v1/projects/{project_id}/validate")
        assert valid_report.status_code == 200, valid_report.text
        assert "VAL-22" not in {issue["rule_id"] for issue in valid_report.json()["issues"]}
        semantic_update = client.patch(
            f"/api/v1/artifacts/{artifact['id']}",
            json={
                "base_revision": 1,
                "reason": "Clarify the visible workflow",
                "title": "Updated payment workflow projection",
            },
        )
        assert semantic_update.status_code == 200, semantic_update.text
        drift_report = client.get(f"/api/v1/projects/{project_id}/validate")
        assert "VAL-22" in {issue["rule_id"] for issue in drift_report.json()["issues"]}

        sketch_projection = client.post(
            f"/api/v1/projects/{project_id}/projections",
            json={
                "view_id": "main",
                "visual_type": "sketch",
                "position": {"x": 700, "y": 200, "w": 300, "h": 180, "z": 3},
                "style": {"scene_json": '{"type":"excalidraw","elements":[]}'},
            },
        )
        assert sketch_projection.status_code == 201, sketch_projection.text
        current_project = client.get(
            f"/api/v1/workspaces/{workspace.json()['id']}/projects"
        ).json()[0]
        promoted = client.post(
            f"/api/v1/projects/{project_id}/projections/{sketch_projection.json()['id']}/promote",
            json={
                "base_revision": current_project["current_revision"],
                "scene_json": '{"type":"excalidraw","elements":[]}',
                "artifact_type": "idea",
                "title": "Promoted canvas sketch",
                "payload": {"content": "A sketch promoted into the project graph."},
            },
        )
        assert promoted.status_code == 201, promoted.text
        promoted_result = promoted.json()
        assert promoted_result["project_revision"] == current_project["current_revision"] + 3
        stored_projection = client.get(f"/api/v1/projects/{project_id}/projections").json()
        promoted_source = next(
            item for item in stored_projection if item["id"] == sketch_projection.json()["id"]
        )
        assert promoted_source["artifact_id"] == promoted_result["sketch_artifact_id"]
        derived_edge = next(
            edge
            for edge in client.get(f"/api/v1/projects/{project_id}/edges").json()
            if edge["id"] == promoted_result["edge_id"]
        )
        assert derived_edge["edge_type"] == "derived_from"
        assert derived_edge["source_id"] == promoted_result["artifact_id"]
        assert derived_edge["target_id"] == promoted_result["sketch_artifact_id"]


def test_edge_pairs_cycles_same_project_and_contradiction_issue() -> None:
    import os
    import secrets

    user_id = f"graph-owner-{secrets.token_hex(4)}"
    app = create_app(settings(), database_url=os.environ["DATABASE_URL"])
    app.state.oidc_client = FakeOIDCClient({"sub": user_id})
    with TestClient(app) as client:
        client.get("/auth/callback", follow_redirects=False)
        workspace = client.post("/api/v1/workspaces", json={"name": "Graph test"})
        assert workspace.status_code == 201
        project = client.post(
            f"/api/v1/workspaces/{workspace.json()['id']}/projects",
            json={"name": "Graph project"},
        )
        assert project.status_code == 201
        project_id = project.json()["id"]

        def create_artifact(kind: str, title: str, payload: dict[str, object]) -> str:
            response = client.post(
                f"/api/v1/projects/{project_id}/artifacts",
                json={"type": kind, "title": title, "payload": payload},
            )
            assert response.status_code == 201, response.text
            return response.json()["id"]

        task_a = create_artifact(
            "task", "Task A", {"title": "A", "acceptance_criteria": [], "depends_on": []}
        )
        task_b = create_artifact(
            "task", "Task B", {"title": "B", "acceptance_criteria": [], "depends_on": []}
        )
        idea = create_artifact("idea", "Idea", {"content": "An alternative approach"})
        project_revision = client.get(f"/api/v1/projects/{project_id}").json()["current_revision"]

        created = client.post(
            f"/api/v1/projects/{project_id}/edges",
            json={
                "base_revision": project_revision,
                "source_id": task_a,
                "target_id": task_b,
                "edge_type": "depends_on",
                "reason": "Task A depends on B",
            },
        )
        assert created.status_code == 201, created.text
        edge = created.json()
        listed_edges = client.get(f"/api/v1/projects/{project_id}/edges")
        assert listed_edges.status_code == 200
        assert listed_edges.json()[0]["id"] == edge["id"]
        assert listed_edges.json()[0]["edge_type"] == "depends_on"

        neighborhood = client.get(
            f"/api/v1/projects/{project_id}/graph/neighborhood",
            params={"artifact_id": task_a, "depth": 1, "direction": "outgoing"},
        )
        assert neighborhood.status_code == 200, neighborhood.text
        assert {node["artifact"]["id"] for node in neighborhood.json()["nodes"]} == {
            task_a,
            task_b,
        }
        impact = client.get(
            f"/api/v1/projects/{project_id}/graph/impact",
            params={"artifact_id": task_b, "depth": 2, "edge_type": "depends_on"},
        )
        assert impact.status_code == 200, impact.text
        assert [node["artifact"]["id"] for node in impact.json()["affected"]] == [task_a]

        invalid_pair = client.post(
            f"/api/v1/projects/{project_id}/edges",
            json={
                "base_revision": project_revision + 1,
                "source_id": idea,
                "target_id": task_a,
                "edge_type": "depends_on",
                "reason": "Invalid endpoint pair",
            },
        )
        assert invalid_pair.status_code == 422
        assert invalid_pair.json()["error"]["code"] == "graph.invalid_edge"

        cycle = client.post(
            f"/api/v1/projects/{project_id}/edges",
            json={
                "base_revision": project_revision + 1,
                "source_id": task_b,
                "target_id": task_a,
                "edge_type": "depends_on",
                "reason": "Would introduce a cycle",
            },
        )
        assert cycle.status_code == 409
        assert cycle.json()["error"]["code"] == "conflict.graph_cycle"

        derived = client.post(
            f"/api/v1/projects/{project_id}/edges",
            json={
                "base_revision": project_revision + 1,
                "source_id": task_a,
                "target_id": task_b,
                "edge_type": "realized_by",
                "reason": "Derived edge cannot be stored",
            },
        )
        assert derived.status_code == 422

        contradiction = client.post(
            f"/api/v1/projects/{project_id}/edges",
            json={
                "base_revision": project_revision + 1,
                "source_id": idea,
                "target_id": task_a,
                "edge_type": "contradicts",
                "reason": "Record conflicting direction",
            },
        )
        assert contradiction.status_code == 201, contradiction.text
        issue_id = contradiction.json()["created_issue_id"]
        issue = client.get(f"/api/v1/artifacts/{issue_id}")
        assert issue.status_code == 200
        assert issue.json()["type"] == "issue"

        requirement = create_artifact(
            "requirement",
            "Traceable requirement",
            {
                "ears_pattern": "ubiquitous",
                "clauses": {"response": "The system displays the saved state."},
                "priority": "should",
                "acceptance_criteria": [],
            },
        )
        component = create_artifact(
            "component",
            "Settings component",
            {"name": "Settings", "responsibility": "Settings", "interfaces": []},
        )
        test_case = create_artifact(
            "test_case",
            "Settings test",
            {"scenario": "Save settings", "expected": "Saved", "linked_artifacts": [requirement]},
        )
        for source_id, target_id, edge_type in (
            (component, requirement, "implements"),
            (requirement, test_case, "validated_by"),
        ):
            current_revision = client.get(f"/api/v1/projects/{project_id}").json()[
                "current_revision"
            ]
            linked = client.post(
                f"/api/v1/projects/{project_id}/edges",
                json={
                    "base_revision": current_revision,
                    "source_id": source_id,
                    "target_id": target_id,
                    "edge_type": edge_type,
                    "reason": "Connect requirement traceability",
                },
            )
            assert linked.status_code == 201, linked.text
        traceability = client.get(
            f"/api/v1/projects/{project_id}/graph/traceability",
            params={"requirement_id": requirement},
        )
        assert traceability.status_code == 200, traceability.text
        assert [item["id"] for item in traceability.json()["components"]] == [component]
        assert [item["id"] for item in traceability.json()["tests"]] == [test_case]
        assert traceability.json()["gaps"] == []

        current_revision = client.get(f"/api/v1/projects/{project_id}").json()["current_revision"]
        deleted = client.delete(
            f"/api/v1/projects/{project_id}/edges/{edge['id']}",
            params={"base_revision": current_revision, "reason": "Remove dependency"},
        )
        assert deleted.status_code == 204
