from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api import deps
from app.api.schemas import (
    AnswerIn,
    AnswerResultOut,
    CreateSessionIn,
    SessionOut,
    SessionSummaryOut,
)
from app.application.sessions import AnswerQuestion, CreateSession, GetSession, ListSessions

router = APIRouter(tags=["sesiones"])


@router.post("/sessions", response_model=SessionOut, status_code=201)
def create_session(
    body: CreateSessionIn,
    db: deps.Db,
    use_case: Annotated[CreateSession, Depends(deps.create_session)],
):
    """Elige las preguntas según el plan y las devuelve sin marcar la correcta."""
    view = use_case.execute(body.mode, [s.to_domain() for s in body.plan])
    db.commit()
    return view


@router.get("/sessions", response_model=list[SessionSummaryOut])
def list_sessions(
    use_case: Annotated[ListSessions, Depends(deps.list_sessions)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """Historial, de la más reciente a la más antigua."""
    return use_case.execute(limit, offset)


@router.get("/sessions/{session_id}", response_model=SessionOut)
def get_session(session_id: int, use_case: Annotated[GetSession, Depends(deps.get_session)]):
    """Una sesión con el mismo orden de opciones que cuando se creó."""
    return use_case.execute(session_id)


@router.post("/sessions/{session_id}/answers", response_model=AnswerResultOut)
def answer(
    session_id: int,
    body: AnswerIn,
    db: deps.Db,
    use_case: Annotated[AnswerQuestion, Depends(deps.answer_question)],
):
    """Registra la respuesta, la califica y devuelve la correcta con su explicación."""
    result = use_case.execute(session_id, body.question_id, body.option_id, body.time_ms)
    db.commit()
    return result
