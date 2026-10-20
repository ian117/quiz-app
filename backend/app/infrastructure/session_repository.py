"""Repositorio de sesiones (session, session_question, answer) sobre SQLAlchemy 2.0."""
from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.errors import AlreadyAnswered
from app.domain.session import Answer, Mode, QuizSession
from app.infrastructure.mappers import plan_from_json, plan_to_json
from app.infrastructure.orm.models import AnswerRow, SessionQuestionRow, SessionRow


class SqlAlchemySessionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, session: QuizSession) -> None:
        row = SessionRow(
            mode=session.mode.value,
            plan=plan_to_json(session.plan),
            started_at=session.started_at,
            total=session.total,
        )
        self._session.add(row)
        self._session.flush()
        self._session.add_all(
            SessionQuestionRow(session_id=row.id, question_id=qid, position=position)
            for position, qid in enumerate(session.question_ids, start=1)
        )
        self._session.flush()
        session.id = row.id

    def get(self, session_id: int) -> QuizSession | None:
        row = self._session.get(SessionRow, session_id)
        return self._load([row])[0] if row else None

    def list_recent(self, limit: int, offset: int) -> list[QuizSession]:
        rows = self._session.scalars(
            select(SessionRow)
            .order_by(SessionRow.started_at.desc(), SessionRow.id.desc())
            .limit(limit)
            .offset(offset)
        ).all()
        return self._load(list(rows))

    def save(self, session: QuizSession) -> None:
        row = self._session.get(SessionRow, session.id)
        row.score = session.score
        row.finished_at = session.finished_at
        new = [a for a in session.answers if a.id is None]
        rows = [
            AnswerRow(
                session_id=session.id,
                question_id=a.question_id,
                option_id=a.option_id,
                is_correct=a.is_correct,
                time_ms=a.time_ms,
            )
            for a in new
        ]
        self._session.add_all(rows)
        try:
            self._session.flush()
        except IntegrityError as exc:
            # Dos respuestas a la vez a la misma pregunta: gana la primera.
            raise AlreadyAnswered(new[0].question_id) from exc
        for answer, answer_row in zip(new, rows, strict=True):
            answer.id = answer_row.id

    def _load(self, rows: list[SessionRow]) -> list[QuizSession]:
        ids = [r.id for r in rows]
        questions: dict[int, list[int]] = defaultdict(list)
        for sq in self._session.scalars(
            select(SessionQuestionRow)
            .where(SessionQuestionRow.session_id.in_(ids))
            .order_by(SessionQuestionRow.session_id, SessionQuestionRow.position)
        ):
            questions[sq.session_id].append(sq.question_id)
        answers: dict[int, list[Answer]] = defaultdict(list)
        for a in self._session.scalars(
            select(AnswerRow).where(AnswerRow.session_id.in_(ids)).order_by(AnswerRow.id)
        ):
            answers[a.session_id].append(
                Answer(a.question_id, a.option_id, a.is_correct, a.time_ms, a.id)
            )
        return [
            QuizSession(
                mode=Mode(r.mode),
                plan=plan_from_json(r.plan),
                question_ids=tuple(questions[r.id]),
                started_at=r.started_at,
                score=r.score,
                finished_at=r.finished_at,
                answers=answers[r.id],
                id=r.id,
            )
            for r in rows
        ]
