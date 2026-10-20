"""Aplicación FastAPI. `uvicorn app.api.main:app`."""
from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from random import Random

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.api.routers import catalog, sessions
from app.api.settings import Settings, cors_origins_from_env
from app.application.errors import EmptySession, SessionNotFound
from app.domain.errors import AlreadyAnswered, DomainError

# Cada error de reglas del juego tiene su código; el resto de DomainError es 422.
_STATUS: dict[type[Exception], int] = {
    SessionNotFound: 404,
    AlreadyAnswered: 409,
    EmptySession: 422,
    DomainError: 422,
}


def _handle(request: Request, exc: Exception) -> JSONResponse:
    status = next(code for cls, code in _STATUS.items() if isinstance(exc, cls))
    return JSONResponse({"detail": str(exc)}, status_code=status)


def create_app(
    engine: Engine | None = None,
    rng_factory: Callable[[], Random] = Random,
) -> FastAPI:
    """Con `engine` (tests) no lee el entorno; sin él, usa DATABASE_URL al arrancar."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if engine is not None:
            app.state.engine = engine
            yield
            return
        app.state.engine = create_engine(Settings.from_env().database_url, pool_pre_ping=True)
        try:
            yield
        finally:
            app.state.engine.dispose()

    app = FastAPI(title="Quiz API", version="0.1.0", lifespan=lifespan)
    app.state.rng_factory = rng_factory

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins_from_env(),
        allow_methods=["GET", "POST"],
        allow_headers=["content-type"],
    )
    for exc_type in (SessionNotFound, AlreadyAnswered, EmptySession, DomainError):
        app.add_exception_handler(exc_type, _handle)

    @app.get("/health", tags=["salud"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(catalog.router)
    app.include_router(sessions.router)
    return app


app = create_app()
