"""Composición: arma los casos de uso con sus adaptadores para cada petición.

La transacción es explícita: los endpoints que escriben llaman a `db.commit()`. Si no hay
commit (o hay una excepción), al cerrar la sesión se descarta todo.
"""
from __future__ import annotations

from collections.abc import Callable, Iterator
from random import Random
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.application.sessions import (
    AnswerQuestion,
    CreateSession,
    GetCatalog,
    GetSession,
    ListSessions,
)
from app.infrastructure.question_reader import SqlAlchemyQuestionReader
from app.infrastructure.session_repository import SqlAlchemySessionRepository


def get_db(request: Request) -> Iterator[Session]:
    with Session(request.app.state.engine) as db:
        yield db


Db = Annotated[Session, Depends(get_db)]


def get_rng_factory(request: Request) -> Callable[[], Random]:
    return request.app.state.rng_factory


def get_catalog(db: Db) -> GetCatalog:
    return GetCatalog(SqlAlchemyQuestionReader(db))


def create_session(
    db: Db, rng_factory: Annotated[Callable[[], Random], Depends(get_rng_factory)]
) -> CreateSession:
    return CreateSession(SqlAlchemyQuestionReader(db), SqlAlchemySessionRepository(db), rng_factory)


def answer_question(db: Db) -> AnswerQuestion:
    return AnswerQuestion(SqlAlchemyQuestionReader(db), SqlAlchemySessionRepository(db))


def get_session(db: Db) -> GetSession:
    return GetSession(SqlAlchemyQuestionReader(db), SqlAlchemySessionRepository(db))


def list_sessions(db: Db) -> ListSessions:
    return ListSessions(SqlAlchemySessionRepository(db))
