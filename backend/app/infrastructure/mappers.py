"""Mappers dominio <-> ORM compartidos por los repositorios."""
from __future__ import annotations

from typing import Any

from app.domain.catalog import Option, Question, Topic
from app.domain.selection import Order, Stretch
from app.infrastructure.orm.models import QuestionRow, TopicRow


def topic_to_domain(row: TopicRow) -> Topic:
    return Topic(slug=row.slug, name=row.name, area=row.area, id=row.id)


def question_to_domain(row: QuestionRow) -> Question:
    return Question(
        key=row.key,
        topic_slug=row.topic.slug,
        position=row.position,
        prompt_md=row.prompt_md,
        explanation_md=row.explanation_md,
        tags={t.slug for t in row.tags},
        options=[
            Option(o.text_md, o.is_correct, o.retired_at, o.id)
            for o in sorted(row.options, key=lambda o: o.id)
        ],
        retired_at=row.retired_at,
        id=row.id,
    )


def plan_to_json(plan: tuple[Stretch, ...]) -> list[dict[str, Any]]:
    """El plan como se guarda en session.plan: las mismas claves que usa la API."""
    return [
        {
            "topic": s.topic,
            "topics": list(s.topics),
            "area": s.area,
            "tags": list(s.tags),
            "n": s.n,
            "order": s.order.value,
        }
        for s in plan
    ]


def plan_from_json(data: list[dict[str, Any]]) -> tuple[Stretch, ...]:
    return tuple(
        Stretch(
            n=d.get("n"),
            order=Order(d.get("order", Order.RANDOM)),
            topic=d.get("topic"),
            topics=tuple(d.get("topics", ())),
            area=d.get("area"),
            tags=tuple(d.get("tags", ())),
        )
        for d in data
    )
