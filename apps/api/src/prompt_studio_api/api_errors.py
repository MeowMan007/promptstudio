from __future__ import annotations

import json
import logging
import re
import time
from collections.abc import Awaitable, Callable
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response

logger = logging.getLogger("prompt_studio.api")
CORRELATION_PATTERN = re.compile(r"[A-Za-z0-9._:-]{1,128}\Z")


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Any
    correlation_id: str
    retryable: bool


class ErrorEnvelope(BaseModel):
    error: ErrorDetail


def request_correlation_id(request: Request) -> str:
    value = getattr(request.state, "correlation_id", None)
    if isinstance(value, str):
        return value
    return str(uuid4())


def _json_log(event: str, **fields: Any) -> None:
    logger.info(json.dumps({"event": event, **fields}, separators=(",", ":")))


def _error_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    details: Any = None,
    retryable: bool = False,
) -> JSONResponse:
    correlation_id = request_correlation_id(request)
    body = ErrorEnvelope(
        error=ErrorDetail(
            code=code,
            message=message,
            details=details or {},
            correlation_id=correlation_id,
            retryable=retryable,
        )
    )
    response = JSONResponse(status_code=status_code, content=body.model_dump(mode="json"))
    response.headers["X-Correlation-ID"] = correlation_id
    if status_code >= 500:
        _json_log(
            "api.error",
            correlation_id=correlation_id,
            status_code=status_code,
            code=code,
            path=request.url.path,
        )
    return response


def _http_error_code(status_code: int) -> str:
    return {
        401: "auth.required",
        403: "auth.forbidden",
        404: "resource.not_found",
        405: "http.method_not_allowed",
        409: "conflict.request",
        429: "rate_limited",
        503: "service.unavailable",
    }.get(status_code, "http.error")


def install_api_conventions(app: FastAPI) -> None:
    @app.middleware("http")
    async def correlation_and_access_log(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        candidate = request.headers.get("x-correlation-id", "")
        correlation_id = candidate if CORRELATION_PATTERN.fullmatch(candidate) else str(uuid4())
        request.state.correlation_id = correlation_id
        started = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        _json_log(
            "api.request",
            correlation_id=correlation_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round((time.perf_counter() - started) * 1000, 2),
        )
        return response

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, str) else "Request could not be completed"
        code = _http_error_code(exc.status_code)
        extra_details: Any = {}
        if isinstance(exc.detail, dict):
            supplied_code = exc.detail.get("code")
            supplied_message = exc.detail.get("message")
            supplied_details = exc.detail.get("details")
            if isinstance(supplied_code, str):
                code = supplied_code
            if isinstance(supplied_message, str):
                detail = supplied_message
            if isinstance(supplied_details, dict):
                extra_details = supplied_details
        return _error_response(
            request,
            status_code=exc.status_code,
            code=code,
            message=detail,
            details=extra_details,
            retryable=exc.status_code in {408, 425, 429, 502, 503, 504},
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = [
            {
                "loc": [str(part) for part in error.get("loc", ())],
                "message": str(error.get("msg", "Invalid value")),
                "code": str(error.get("type", "value_error")),
            }
            for error in exc.errors()
        ]
        return _error_response(
            request,
            status_code=422,
            code="request.validation",
            message="Request validation failed",
            details={"issues": errors},
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, _: Exception) -> JSONResponse:
        return _error_response(
            request,
            status_code=500,
            code="internal.error",
            message="An unexpected error occurred",
            details={},
            retryable=False,
        )
