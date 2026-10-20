"""Constructores y dobles en memoria para los tests unitarios."""
from __future__ import annotations

import copy
from datetime import UTC, datetime

from app.application.ports import InvalidQuiz
from app.application.views import CatalogView
from app.domain.catalog import (
    Catalog,
    OptionSpec,
    QuestionSpec,
    QuizSnapshot,
    TopicSpec,
)
from app.domain.catalog import Question as StoredQuestion
from app.domain.selection import Candidate
from app.domain.session import QuizSession

T0 = datetime(2026, 1, 1, tzinfo=UTC)
T1 = datetime(2026, 2, 1, tzinfo=UTC)


def question(
    key: str = "react-uno",
    *,
    topic: str = "react",
    position: int = 1,
    options: tuple[tuple[str, bool], ...] = (("A", True), ("B", False), ("C", False), ("D", False)),
    tags: tuple[str, ...] = (),
    prompt: str = "¿Pregunta?",
    explanation: str = "Porque sí.",
) -> QuestionSpec:
    return QuestionSpec(
        key=key,
        topic_slug=topic,
        position=position,
        prompt_md=prompt,
        explanation_md=explanation,
        options=tuple(OptionSpec(text, correct) for text, correct in options),
        tags=tags,
    )


def snapshot(*questions: QuestionSpec, area: str = "frontend") -> QuizSnapshot:
    slugs = dict.fromkeys(q.topic_slug for q in questions)
    return QuizSnapshot(tuple(TopicSpec(s, area) for s in slugs), questions)


class StaticQuizSource:
    def __init__(self, snap: QuizSnapshot | InvalidQuiz) -> None:
        self.snap = snap

    def load(self) -> QuizSnapshot:
        if isinstance(self.snap, InvalidQuiz):
            raise self.snap
        return self.snap


class InMemoryCatalogRepository:
    def __init__(self) -> None:
        self.stored = Catalog([], [])
        self.loads = 0
        self.saves = 0

    def load(self) -> Catalog:
        self.loads += 1
        return copy.deepcopy(self.stored)

    def save(self, catalog: Catalog) -> None:
        self.saves += 1
        self.stored = copy.deepcopy(catalog)


class InMemoryQuestionReader:
    def __init__(self, *questions: StoredQuestion, areas: dict[str, str] | None = None) -> None:
        self.questions = {q.id: q for q in questions}
        self.areas = areas or {}

    def candidates(self) -> list[Candidate]:
        return [
            Candidate(
                q.id, q.topic_slug, self.areas.get(q.topic_slug, "frontend"), q.position,
                frozenset(q.tags),
            )
            for q in self.questions.values()
            if q.retired_at is None
        ]

    def get_many(self, question_ids) -> dict[int, StoredQuestion]:
        return {i: self.questions[i] for i in question_ids}

    def catalog(self) -> CatalogView:
        return CatalogView((), (), ())


class InMemorySessionRepository:
    def __init__(self) -> None:
        self.sessions: dict[int, QuizSession] = {}

    def add(self, session: QuizSession) -> None:
        session.id = len(self.sessions) + 1
        self.sessions[session.id] = copy.deepcopy(session)

    def get(self, session_id: int) -> QuizSession | None:
        found = self.sessions.get(session_id)
        return copy.deepcopy(found) if found else None

    def save(self, session: QuizSession) -> None:
        self.sessions[session.id] = copy.deepcopy(session)

    def list_recent(self, limit: int, offset: int) -> list[QuizSession]:
        newest_first = sorted(self.sessions.values(), key=lambda s: s.id, reverse=True)
        return copy.deepcopy(newest_first[offset : offset + limit])
