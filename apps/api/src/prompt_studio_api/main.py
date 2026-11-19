from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncEngine

from backend.app.database import create_session_factory
from prompt_studio_api.api_errors import install_api_conventions
from prompt_studio_api.artifacts import router as artifact_router
from prompt_studio_api.edges import router as edge_router
from prompt_studio_api.graph_queries import router as graph_query_router
from prompt_studio_api.identity.oidc import AuthSettings, configure_identity
from prompt_studio_api.projections import router as projection_router
from prompt_studio_api.studio_api import router as studio_api_router
from prompt_studio_api.pages_html import (
    DASHBOARD_HTML,
    DOCS_HTML,
    LANDING_HTML,
    LOGIN_HTML,
    PRICING_HTML,
    TEMPLATES_HTML,
)
from prompt_studio_api.studio_html import STUDIO_HTML
from prompt_studio_api.validation_api import router as validation_router
from prompt_studio_api.workspaces import router as workspace_router


def create_app(
    settings: AuthSettings | None = None,
    *,
    database_url: str | None = None,
) -> FastAPI:
    configured_database_url = database_url or os.getenv("DATABASE_URL")
    engine: AsyncEngine | None = None
    factory = None
    if configured_database_url:
        engine, factory = create_session_factory(configured_database_url)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        if engine is not None:
            await engine.dispose()

    application = FastAPI(title="Prompt Studio API", version="0.1.0", lifespan=lifespan)
    application.state.db_engine = engine
    application.state.db_session_factory = factory
    auth_settings = settings or AuthSettings.from_environment()
    configure_identity(application, auth_settings)
    install_api_conventions(application)
    application.include_router(workspace_router)
    application.include_router(artifact_router)
    application.include_router(edge_router)
    application.include_router(graph_query_router)
    application.include_router(validation_router)
    application.include_router(projection_router)
    application.include_router(studio_api_router)

    @application.get("/health", tags=["operations"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/", response_class=HTMLResponse, tags=["web"])
    async def web_landing() -> HTMLResponse:
        return HTMLResponse(content=LANDING_HTML)

    @application.get("/board", response_class=HTMLResponse, tags=["web"])
    async def web_board() -> HTMLResponse:
        return HTMLResponse(content=STUDIO_HTML)

    @application.get("/templates", response_class=HTMLResponse, tags=["web"])
    async def web_templates() -> HTMLResponse:
        return HTMLResponse(content=TEMPLATES_HTML)

    @application.get("/guide", response_class=HTMLResponse, tags=["web"])
    async def web_guide() -> HTMLResponse:
        return HTMLResponse(content=DOCS_HTML)

    @application.get("/pricing", response_class=HTMLResponse, tags=["web"])
    async def web_pricing() -> HTMLResponse:
        return HTMLResponse(content=PRICING_HTML)

    @application.get("/dashboard", response_class=HTMLResponse, tags=["web"])
    async def web_dashboard() -> HTMLResponse:
        return HTMLResponse(content=DASHBOARD_HTML)

    @application.get("/login", response_class=HTMLResponse, tags=["web"])
    async def web_login() -> HTMLResponse:
        return HTMLResponse(content=LOGIN_HTML)

    @application.get("/signin", response_class=HTMLResponse, tags=["web"])
    async def web_signin() -> HTMLResponse:
        return HTMLResponse(content=LOGIN_HTML)

    return application


app = create_app()
