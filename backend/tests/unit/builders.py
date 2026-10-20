"""Constructores y dobles en memoria para los tests unitarios."""
from __future__ import annotations

import copy
from datetime import UTC, datetime

from app.application.ports import InvalidQuiz
from app.domain.catalog import (
    Catalog,
    OptionSpec,
    QuestionSpec,
    QuizSnapshot,
    TopicSpec,
)

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
