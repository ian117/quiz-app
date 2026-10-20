"""Lectura de preguntas para jugar: candidatas, detalle y conteos del catálogo."""
from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.application.views import AreaCount, CatalogView, TagCount, TopicCount
from app.domain.catalog import Question
from app.domain.selection import Candidate
from app.infrastructure.mappers import question_to_domain
from app.infrastructure.orm.models import QuestionRow, TagRow, TopicRow, question_tag


class SqlAlchemyQuestionReader:
    def __init__(self, session: Session) -> None:
        self._session = session

    def candidates(self) -> list[Candidate]:
        rows = self._session.scalars(
            select(QuestionRow)
            .where(QuestionRow.retired_at.is_(None))
            .options(joinedload(QuestionRow.topic), selectinload(QuestionRow.tags))
        ).all()
        return [
            Candidate(
                question_id=r.id,
                topic_slug=r.topic.slug,
                area=r.topic.area,
                position=r.position,
                tags=frozenset(t.slug for t in r.tags),
            )
            for r in rows
        ]

    def get_many(self, question_ids: Sequence[int]) -> dict[int, Question]:
        rows = self._session.scalars(
            select(QuestionRow)
            .where(QuestionRow.id.in_(question_ids))
            .options(
                joinedload(QuestionRow.topic),
                selectinload(QuestionRow.tags),
                selectinload(QuestionRow.options),
            )
        ).all()
        return {r.id: question_to_domain(r) for r in rows}

    def catalog(self) -> CatalogView:
        active = func.count(QuestionRow.id).filter(QuestionRow.retired_at.is_(None))

        topic_rows = self._session.execute(
            select(TopicRow.slug, TopicRow.name, TopicRow.area, active)
            .join(QuestionRow, QuestionRow.topic_id == TopicRow.id, isouter=True)
            .group_by(TopicRow.id)
            .order_by(TopicRow.area, TopicRow.slug)
        ).all()
        topics = tuple(TopicCount(*row) for row in topic_rows)

        areas: dict[str, int] = {}
        for t in topics:
            areas[t.area] = areas.get(t.area, 0) + t.question_count

        tag_rows = self._session.execute(
            select(TagRow.slug, active)
            .join(question_tag, question_tag.c.tag_id == TagRow.id, isouter=True)
            .join(QuestionRow, QuestionRow.id == question_tag.c.question_id, isouter=True)
            .group_by(TagRow.id)
            .order_by(TagRow.slug)
        ).all()

        return CatalogView(
            areas=tuple(AreaCount(slug, count) for slug, count in sorted(areas.items())),
            topics=topics,
            tags=tuple(TagCount(*row) for row in tag_rows),
        )
