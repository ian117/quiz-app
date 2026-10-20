"""Casos de uso del juego: crear una sesión, responder, consultar el historial."""
from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from random import Random

from app.application.errors import EmptySession, SessionNotFound
from app.application.ports import QuestionReader, SessionRepository
from app.application.views import (
    AnswerResult,
    CatalogView,
    SessionSummary,
    SessionView,
    answer_view,
    session_summary,
    session_view,
)
from app.domain.errors import QuestionNotInSession
from app.domain.selection import Stretch, select_questions
from app.domain.session import Mode, QuizSession


def _now() -> datetime:
    return datetime.now(UTC)


class GetCatalog:
    def __init__(self, questions: QuestionReader) -> None:
        self._questions = questions

    def execute(self) -> CatalogView:
        return self._questions.catalog()


class CreateSession:
    def __init__(
        self,
        questions: QuestionReader,
        sessions: SessionRepository,
        rng_factory: Callable[[], Random] = Random,
        clock: Callable[[], datetime] = _now,
    ) -> None:
        self._questions = questions
        self._sessions = sessions
        self._rng_factory = rng_factory
        self._clock = clock

    def execute(self, mode: Mode, plan: Sequence[Stretch]) -> SessionView:
        ids = select_questions(self._questions.candidates(), plan, self._rng_factory())
        if not ids:
            raise EmptySession
        session = QuizSession(mode, tuple(plan), tuple(ids), started_at=self._clock())
        self._sessions.add(session)
        return session_view(session, self._questions.get_many(ids))


class AnswerQuestion:
    def __init__(
        self,
        questions: QuestionReader,
        sessions: SessionRepository,
        clock: Callable[[], datetime] = _now,
    ) -> None:
        self._questions = questions
        self._sessions = sessions
        self._clock = clock

    def execute(
        self, session_id: int, question_id: int, option_id: int, time_ms: int
    ) -> AnswerResult:
        session = self._sessions.get(session_id)
        if session is None:
            raise SessionNotFound(session_id)
        if question_id not in session.question_ids:
            raise QuestionNotInSession(question_id)
        question = self._questions.get_many([question_id])[question_id]
        answer = session.answer(question, option_id, time_ms, self._clock())
        self._sessions.save(session)
        return AnswerResult(
            answer=answer_view(answer, question),
            score=session.score,
            answered=len(session.answers),
            total=session.total,
            finished=session.finished,
        )


class GetSession:
    def __init__(self, questions: QuestionReader, sessions: SessionRepository) -> None:
        self._questions = questions
        self._sessions = sessions

    def execute(self, session_id: int) -> SessionView:
        session = self._sessions.get(session_id)
        if session is None:
            raise SessionNotFound(session_id)
        return session_view(session, self._questions.get_many(session.question_ids))


class ListSessions:
    def __init__(self, sessions: SessionRepository) -> None:
        self._sessions = sessions

    def execute(self, limit: int = 50, offset: int = 0) -> list[SessionSummary]:
        return [session_summary(s) for s in self._sessions.list_recent(limit, offset)]
