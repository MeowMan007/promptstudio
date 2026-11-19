from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from prompt_studio_api.identity.oidc import AuthSettings
from prompt_studio_api.main import create_app


@pytest.fixture
def client() -> TestClient:
    settings = AuthSettings(
        issuer=None,
        client_id=None,
        client_secret=None,
        redirect_uri=None,
        session_secret_key="secret-key-that-is-at-least-32-chars-long",
    )
    app = create_app(settings)
    return TestClient(app)


def test_landing_page(client: TestClient) -> None:
    res = client.get("/")
    assert res.status_code == 200
    assert "Prompt Studio" in res.text
    assert "/login" in res.text
    assert "btn-magic" not in res.text


def test_login_page(client: TestClient) -> None:
    res = client.get("/login")
    assert res.status_code == 200
    assert "Sign in to workspace" in res.text
    assert "Continue with GitHub" in res.text
    assert "Continue with Google" in res.text
    assert "Work Email" in res.text
    assert "Remember this session" in res.text


def test_signin_alias(client: TestClient) -> None:
    res = client.get("/signin")
    assert res.status_code == 200
    assert "Sign in to workspace" in res.text


def test_board_page(client: TestClient) -> None:
    res = client.get("/board")
    assert res.status_code == 200
    assert "btn-magic" not in res.text
    assert "btn-blueprints-nav" in res.text
    assert "card-btn-sparkle" not in res.text


def test_templates_page(client: TestClient) -> None:
    res = client.get("/templates")
    assert res.status_code == 200
    assert "Architecture Blueprints" in res.text
    assert "/login" in res.text


def test_docs_page(client: TestClient) -> None:
    res = client.get("/guide")
    assert res.status_code == 200
    assert "Prompt Studio Documentation" in res.text
    assert "/login" in res.text


def test_pricing_page(client: TestClient) -> None:
    res = client.get("/pricing")
    assert res.status_code == 200
    assert "Simple, transparent pricing" in res.text
    assert "/login" in res.text


def test_dashboard_page(client: TestClient) -> None:
    res = client.get("/dashboard")
    assert res.status_code == 200
    assert "Dashboard" in res.text
    assert "/login" in res.text
