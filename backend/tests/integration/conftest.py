"""Fixtures de integración: Postgres de docker compose, en una base APARTE (quiz_test).

Nunca se usa la base `quiz`: guarda el historial y no se puede reconstruir.
Variable opcional: TEST_DATABASE_URL (por defecto, el db de compose en localhost).
"""
from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, Engine, make_url
from sqlalchemy.exc import OperationalError

from alembic import command
from app.infrastructure.orm.models import Base

from .helpers import Quiz

BACKEND = Path(__file__).resolve().parents[2]
DEFAULT_URL = "postgresql+psycopg://quiz:quiz@localhost:5432/quiz_test"


def _test_url() -> URL:
    url = make_url(os.environ.get("TEST_DATABASE_URL", DEFAULT_URL))
    if url.database in (None, "", "quiz", "postgres"):
        raise RuntimeError(f"La base de pruebas no puede ser '{url.database}' (usa quiz_test)")
    return url


@pytest.fixture(scope="session")
def database_url() -> str:
    url = _test_url()
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    try:
        with admin.connect() as conn:
            exists = conn.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": url.database}
            )
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{url.database}"'))
    except OperationalError:
        pytest.skip("Postgres no disponible: levántalo con `docker compose up -d db`")
    finally:
        admin.dispose()

    # Siempre desde cero, con las migraciones reales: así también se prueban.
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    engine.dispose()

    previous = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = url.render_as_string(hide_password=False)
    try:
        command.upgrade(Config(str(BACKEND / "alembic.ini")), "head")
    finally:
        if previous is None:
            del os.environ["DATABASE_URL"]
        else:
            os.environ["DATABASE_URL"] = previous
    return url.render_as_string(hide_password=False)


@pytest.fixture
def engine(database_url: str) -> Iterator[Engine]:
    engine = create_engine(database_url)
    tables = ", ".join(f'"{t.name}"' for t in Base.metadata.sorted_tables)
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
    yield engine
    engine.dispose()


@pytest.fixture
def quiz(tmp_path: Path, engine: Engine, database_url: str, monkeypatch) -> Quiz:
    return Quiz(tmp_path, database_url, monkeypatch)
