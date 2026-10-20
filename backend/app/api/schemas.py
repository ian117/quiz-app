"""Schemas Pydantic de la API: el contrato que ve el frontend (OpenAPI).

Las opciones y preguntas sin responder no tienen campo `is_correct`: lo que no está en el
schema no puede salir en la respuesta.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.selection import Order, Stretch
from app.domain.session import Mode


class StretchIn(BaseModel):
    """Un tramo del plan. Los filtros se combinan con AND; los valores de una lista, con OR."""

    model_config = ConfigDict(extra="forbid")

    topic: str | None = None
    topics: list[str] = []
    area: str | None = None
    tags: list[str] = []
    n: int | None = Field(None, ge=1, description="Cuántas preguntas; ausente = todas")
    order: Order = Order.RANDOM

    def to_domain(self) -> Stretch:
        return Stretch(
            n=self.n,
            order=self.order,
            topic=self.topic,
            topics=tuple(self.topics),
            area=self.area,
            tags=tuple(self.tags),
        )


class CreateSessionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Mode
    plan: list[StretchIn] = Field(min_length=1, max_length=20)


class AnswerIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: int
    option_id: int
    time_ms: int = Field(ge=0)


class StretchOut(BaseModel):
    topic: str | None
    topics: list[str]
    area: str | None
    tags: list[str]
    n: int | None
    order: Order


class OptionOut(BaseModel):
    id: int
    text_md: str


class AnswerOut(BaseModel):
    question_id: int
    option_id: int
    is_correct: bool
    correct_option_id: int
    explanation_md: str
    time_ms: int


class QuestionOut(BaseModel):
    id: int
    key: str
    topic: str
    position: int
    prompt_md: str
    tags: list[str]
    options: list[OptionOut]
    answer: AnswerOut | None = Field(
        description="Solo si ya se respondió: aquí, y solo aquí, viene la correcta"
    )


class SessionOut(BaseModel):
    id: int
    mode: Mode
    plan: list[StretchOut]
    started_at: datetime
    finished_at: datetime | None
    score: int
    total: int
    answered: int
    questions: list[QuestionOut]


class SessionSummaryOut(BaseModel):
    id: int
    mode: Mode
    started_at: datetime
    finished_at: datetime | None
    score: int
    total: int
    answered: int


class AnswerResultOut(BaseModel):
    answer: AnswerOut
    score: int
    answered: int
    total: int
    finished: bool


class AreaOut(BaseModel):
    slug: str
    question_count: int


class TopicOut(BaseModel):
    slug: str
    name: str
    area: str
    question_count: int


class TagOut(BaseModel):
    slug: str
    question_count: int


class CatalogOut(BaseModel):
    areas: list[AreaOut]
    topics: list[TopicOut]
    tags: list[TagOut]
