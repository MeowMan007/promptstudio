from __future__ import annotations

import os
import secrets
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast

from authlib.integrations.base_client.errors import OAuthError  # type: ignore[import-untyped]
from authlib.integrations.starlette_client import OAuth  # type: ignore[import-untyped]
from fastapi import APIRouter, FastAPI, HTTPException, Request, Response
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse


@dataclass(frozen=True)
class AuthSettings:
    issuer: str | None
    client_id: str | None
    client_secret: str | None
    redirect_uri: str | None
    session_secret_key: str
    session_ttl_seconds: int = 3600
    session_cookie_secure: bool = False
    post_login_redirect: str = "/"

    @property
    def oidc_configured(self) -> bool:
        return bool(self.issuer and self.client_id and self.client_secret)

    @classmethod
    def from_environment(cls) -> AuthSettings:
        environment = os.getenv("APP_ENV", "development").lower()
        session_secret = os.getenv("SESSION_SECRET_KEY")
        if not session_secret:
            if environment == "production":
                raise RuntimeError("SESSION_SECRET_KEY must be set in production")
            session_secret = secrets.token_urlsafe(48)
        if len(session_secret) < 32:
            raise RuntimeError("SESSION_SECRET_KEY must contain at least 32 characters")

        ttl = int(os.getenv("SESSION_TTL_SECONDS", "3600"))
        if ttl < 60:
            raise RuntimeError("SESSION_TTL_SECONDS must be at least 60")

        post_login_redirect = os.getenv("POST_LOGIN_REDIRECT", "/")
        if not post_login_redirect.startswith("/") or post_login_redirect.startswith("//"):
            raise RuntimeError("POST_LOGIN_REDIRECT must be a relative path")

        oidc_values = (
            os.getenv("OIDC_ISSUER") or None,
            os.getenv("OIDC_CLIENT_ID") or None,
            os.getenv("OIDC_CLIENT_SECRET") or None,
        )
        if any(oidc_values) and not all(oidc_values):
            raise RuntimeError("OIDC issuer, client id, and client secret must be set together")

        secure_cookie_value = os.getenv("SESSION_COOKIE_SECURE")
        secure_cookie = (
            secure_cookie_value.lower() in {"true", "1", "yes"}
            if secure_cookie_value is not None
            else environment == "production"
        )
        if environment == "production" and not secure_cookie:
            raise RuntimeError("SESSION_COOKIE_SECURE must be enabled in production")

        return cls(
            issuer=oidc_values[0],
            client_id=oidc_values[1],
            client_secret=oidc_values[2],
            redirect_uri=os.getenv("OIDC_REDIRECT_URI") or None,
            session_secret_key=session_secret,
            session_ttl_seconds=ttl,
            session_cookie_secure=secure_cookie,
            post_login_redirect=post_login_redirect,
        )


class SessionUser(BaseModel):
    sub: str


class SessionResponse(BaseModel):
    user: SessionUser
    expires_at: int


def create_oidc_client(settings: AuthSettings) -> Any | None:
    if not settings.oidc_configured:
        return None

    issuer = settings.issuer.rstrip("/") if settings.issuer else ""
    oauth = OAuth()
    oauth.register(
        name="identity_provider",
        client_id=settings.client_id,
        client_secret=settings.client_secret,
        server_metadata_url=f"{issuer}/.well-known/openid-configuration",
        client_kwargs={"scope": "openid profile email"},
    )
    return oauth.create_client("identity_provider")


def install_session_middleware(app: FastAPI, settings: AuthSettings) -> None:
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret_key,
        session_cookie="prompt_studio_session",
        max_age=settings.session_ttl_seconds,
        same_site="lax",
        https_only=settings.session_cookie_secure,
    )


def create_auth_router(settings: AuthSettings) -> APIRouter:
    router = APIRouter(prefix="/auth", tags=["identity"])

    @router.get("/login", name="oidc_login")
    async def login(request: Request) -> Response:
        client = request.app.state.oidc_client
        if client is None:
            raise HTTPException(status_code=503, detail="OIDC provider is not configured")
        redirect_uri = settings.redirect_uri or str(request.url_for("oidc_callback"))
        try:
            return cast(Response, await client.authorize_redirect(request, redirect_uri))
        except Exception as exc:
            raise HTTPException(status_code=502, detail="OIDC provider unavailable") from exc

    @router.get("/callback", name="oidc_callback")
    async def callback(request: Request) -> RedirectResponse:
        client = request.app.state.oidc_client
        if client is None:
            raise HTTPException(status_code=503, detail="OIDC provider is not configured")
        try:
            token = await client.authorize_access_token(request)
        except OAuthError as exc:
            request.session.clear()
            raise HTTPException(status_code=401, detail="OIDC login was not accepted") from exc
        except Exception as exc:
            request.session.clear()
            raise HTTPException(status_code=502, detail="OIDC provider unavailable") from exc

        userinfo = token.get("userinfo")
        if not isinstance(userinfo, dict) or not isinstance(userinfo.get("sub"), str):
            request.session.clear()
            raise HTTPException(status_code=401, detail="OIDC provider returned no subject")

        expires_at = int(request.app.state.clock()) + settings.session_ttl_seconds
        request.session.clear()
        request.session.update({"user": {"sub": userinfo["sub"]}, "expires_at": expires_at})
        return RedirectResponse(settings.post_login_redirect, status_code=303)

    @router.get("/me", response_model=SessionResponse)
    async def current_session(request: Request) -> SessionResponse:
        user = request.session.get("user")
        expires_at = request.session.get("expires_at")
        now = int(request.app.state.clock())
        if not isinstance(user, dict) or not isinstance(expires_at, int) or expires_at <= now:
            request.session.clear()
            raise HTTPException(status_code=401, detail="Authentication required")
        return SessionResponse(user=SessionUser.model_validate(user), expires_at=expires_at)

    @router.post("/logout", status_code=204)
    async def logout(request: Request) -> Response:
        request.session.clear()
        return Response(status_code=204)

    return router


def configure_identity(
    app: FastAPI,
    settings: AuthSettings,
    *,
    clock: Callable[[], float] = time.time,
) -> None:
    install_session_middleware(app, settings)
    app.state.oidc_client = create_oidc_client(settings)
    app.state.clock = clock
    app.include_router(create_auth_router(settings))
