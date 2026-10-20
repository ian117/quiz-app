"""Modelo de datos (docs/vision.md, "Modelo de datos").

Nada de lo que tiene historial se borra: las FK hacia question y option no llevan
ON DELETE CASCADE, y retirar es poner retired_at.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# Nombres de constraints predecibles: Alembic los necesita para poder modificarlos después.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    type_annotation_map = {datetime: DateTime(timezone=True)}


question_tag = Table(
    "question_tag",
    Base.metadata,
    Column("question_id", ForeignKey("question.id"), primary_key=True),
    Column("tag_id", ForeignKey("tag.id"), primary_key=True),
)


class TopicRow(Base):
    __tablename__ = "topic"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    area: Mapped[str] = mapped_column(String(50), index=True)


class TagRow(Base):
    __tablename__ = "tag"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True)


class QuestionRow(Base):
    __tablename__ = "question"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(200), unique=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topic.id"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    prompt_md: Mapped[str] = mapped_column(Text)
    explanation_md: Mapped[str] = mapped_column(Text)
    retired_at: Mapped[datetime | None]

    topic: Mapped[TopicRow] = relationship()
    options: Mapped[list[OptionRow]] = relationship(back_populates="question")
    tags: Mapped[list[TagRow]] = relationship(secondary=question_tag)


class OptionRow(Base):
    __tablename__ = "option"
    # La identidad de una opción es su texto dentro de la pregunta.
    __table_args__ = (
        UniqueConstraint("question_id", "text_md", name="uq_option_question_id_text_md"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("question.id"))
    text_md: Mapped[str] = mapped_column(Text)
    is_correct: Mapped[bool] = mapped_column(Boolean)
    retired_at: Mapped[datetime | None]

    question: Mapped[QuestionRow] = relationship(back_populates="options")


class SessionRow(Base):
    __tablename__ = "session"

    id: Mapped[int] = mapped_column(primary_key=True)
    mode: Mapped[str] = mapped_column(String(50))
    plan: Mapped[Any] = mapped_column(JSONB)
    started_at: Mapped[datetime] = mapped_column(server_default=func.now())
    finished_at: Mapped[datetime | None]
    score: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    total: Mapped[int] = mapped_column(Integer)


class SessionQuestionRow(Base):
    """Qué preguntas salieron en la sesión, aunque no se hayan respondido."""

    __tablename__ = "session_question"

    session_id: Mapped[int] = mapped_column(ForeignKey("session.id"), primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("question.id"), primary_key=True)
    position: Mapped[int] = mapped_column(Integer)


class AnswerRow(Base):
    __tablename__ = "answer"
    __table_args__ = (
        # Solo se responde lo que salió en la sesión, y una vez.
        ForeignKeyConstraint(
            ["session_id", "question_id"],
            ["session_question.session_id", "session_question.question_id"],
        ),
        UniqueConstraint("session_id", "question_id", name="uq_answer_session_id_question_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(Integer)
    question_id: Mapped[int] = mapped_column(Integer, index=True)
    option_id: Mapped[int] = mapped_column(ForeignKey("option.id"))
    is_correct: Mapped[bool] = mapped_column(Boolean)
    time_ms: Mapped[int] = mapped_column(Integer)
