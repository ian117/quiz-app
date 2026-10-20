"""Lo que los casos de uso devuelven a quien los llama.

Aquí vive la regla de no revelar: una pregunta sin responder no lleva `is_correct`,
`correct_option_id` ni explicación. Solo `AnswerView` los trae.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.catalog import Question
from app.domain.selection import Stretch
from app.domain.session import Answer, Mode, QuizSession
from app.domain.shuffle import shuffle_option_ids


@dataclass(frozen=True)
class OptionView:
    id: int
    text_md: str


@dataclass(frozen=True)
class AnswerView:
    question_id: int
    option_id: int
    is_correct: bool
    correct_option_id: int
    explanation_md: str
    time_ms: int


@dataclass(frozen=True)
class QuestionView:
    id: int
    key: str
    topic: str
    position: int
    prompt_md: str
    tags: tuple[str, ...]
    options: tuple[OptionView, ...]
    answer: AnswerView | None


@dataclass(frozen=True)
class SessionView:
    id: int
    mode: Mode
    plan: tuple[Stretch, ...]
    started_at: datetime
    finished_at: datetime | None
    score: int
    total: int
    answered: int
    questions: tuple[QuestionView, ...]


@dataclass(frozen=True)
class SessionSummary:
    id: int
    mode: Mode
    started_at: datetime
    finished_at: datetime | None
    score: int
    total: int
    answered: int


@dataclass(frozen=True)
class AnswerResult:
    answer: AnswerView
    score: int
    answered: int
    total: int
    finished: bool


@dataclass(frozen=True)
class AreaCount:
    slug: str
    question_count: int


@dataclass(frozen=True)
class TopicCount:
    slug: str
    name: str
    area: str
    question_count: int


@dataclass(frozen=True)
class TagCount:
    slug: str
    question_count: int


@dataclass(frozen=True)
class CatalogView:
    areas: tuple[AreaCount, ...]
    topics: tuple[TopicCount, ...]
    tags: tuple[TagCount, ...]


def _saved(entity_id: int | None) -> int:
    """El id de algo que ya viene de la base de datos."""
    if entity_id is None:
        raise ValueError("falta el id: la entidad no se ha guardado")
    return entity_id


def answer_view(answer: Answer, question: Question) -> AnswerView:
    correct = [o for o in question.options if o.is_correct]
    # Si la correcta se retiró después, sigue valiendo la que se vio; si no, la activa.
    active = [o for o in correct if o.retired_at is None]
    return AnswerView(
        question_id=answer.question_id,
        option_id=answer.option_id,
        is_correct=answer.is_correct,
        correct_option_id=_saved((active or correct)[0].id),
        explanation_md=question.explanation_md,
        time_ms=answer.time_ms,
    )


def question_view(session: QuizSession, position: int, question: Question) -> QuestionView:
    question_id, session_id = _saved(question.id), _saved(session.id)
    answer = session.answer_for(question_id)
    # Opciones activas, y la que se respondió aunque se haya retirado después.
    visible = [
        o
        for o in question.options
        if o.retired_at is None or (answer is not None and o.id == answer.option_id)
    ]
    by_id = {_saved(o.id): o for o in visible}
    order = shuffle_option_ids(list(by_id), session_id, question_id)
    return QuestionView(
        id=question_id,
        key=question.key,
        topic=question.topic_slug,
        position=position,
        prompt_md=question.prompt_md,
        tags=tuple(sorted(question.tags)),
        options=tuple(OptionView(i, by_id[i].text_md) for i in order),
        answer=answer_view(answer, question) if answer else None,
    )


def session_view(session: QuizSession, questions: dict[int, Question]) -> SessionView:
    return SessionView(
        id=_saved(session.id),
        mode=session.mode,
        plan=session.plan,
        started_at=session.started_at,
        finished_at=session.finished_at,
        score=session.score,
        total=session.total,
        answered=len(session.answers),
        questions=tuple(
            question_view(session, position, questions[qid])
            for position, qid in enumerate(session.question_ids, start=1)
        ),
    )


def session_summary(session: QuizSession) -> SessionSummary:
    return SessionSummary(
        id=_saved(session.id),
        mode=session.mode,
        started_at=session.started_at,
        finished_at=session.finished_at,
        score=session.score,
        total=session.total,
        answered=len(session.answers),
    )
