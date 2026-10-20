"""Repositorio del catálogo sobre SQLAlchemy 2.0, con el mapper dominio <-> ORM."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.domain.catalog import Catalog, Option, Question, Topic
from app.infrastructure.orm.models import OptionRow, QuestionRow, TagRow, TopicRow

# --- mapper -------------------------------------------------------------------------


def _topic_to_domain(row: TopicRow) -> Topic:
    return Topic(slug=row.slug, name=row.name, area=row.area, id=row.id)


def _question_to_domain(row: QuestionRow) -> Question:
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


class SqlAlchemyCatalogRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def load(self) -> Catalog:
        topics = self._session.scalars(select(TopicRow)).all()
        questions = self._session.scalars(
            select(QuestionRow).options(
                selectinload(QuestionRow.topic),
                selectinload(QuestionRow.tags),
                selectinload(QuestionRow.options),
            )
        ).all()
        return Catalog(
            [_topic_to_domain(t) for t in topics],
            [_question_to_domain(q) for q in questions],
        )

    def save(self, catalog: Catalog) -> None:
        # Las filas cargadas en load() siguen en el identity map de la sesión: aquí solo se
        # copian los valores, y SQLAlchemy emite UPDATE únicamente donde algo cambió.
        topic_rows = self._save_topics(catalog)
        tag_rows = {t.slug: t for t in self._session.scalars(select(TagRow))}

        for q in catalog.questions.values():
            row = self._session.get(QuestionRow, q.id) if q.id is not None else QuestionRow()
            row.key = q.key
            row.topic = topic_rows[q.topic_slug]
            row.position = q.position
            row.prompt_md = q.prompt_md
            row.explanation_md = q.explanation_md
            row.retired_at = q.retired_at

            if {t.slug for t in row.tags} != q.tags:
                for slug in q.tags - tag_rows.keys():
                    tag_rows[slug] = TagRow(slug=slug)
                row.tags = [tag_rows[slug] for slug in sorted(q.tags)]

            self._save_options(row, q)
            self._session.add(row)

        self._session.flush()

    def _save_topics(self, catalog: Catalog) -> dict[str, TopicRow]:
        rows: dict[str, TopicRow] = {}
        for t in catalog.topics.values():
            row = self._session.get(TopicRow, t.id) if t.id is not None else TopicRow()
            row.slug, row.name, row.area = t.slug, t.name, t.area
            self._session.add(row)
            rows[t.slug] = row
        return rows

    def _save_options(self, question_row: QuestionRow, q: Question) -> None:
        existing = {o.id: o for o in question_row.options}
        for o in q.options:
            row = existing[o.id] if o.id is not None else OptionRow()
            row.text_md, row.is_correct, row.retired_at = o.text_md, o.is_correct, o.retired_at
            if o.id is None:
                question_row.options.append(row)
