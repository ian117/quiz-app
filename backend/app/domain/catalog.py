"""Catálogo del quiz: entidades puras y la regla que lo reconcilia con el markdown.

Regla central, igual para preguntas y opciones: nunca se borra, se retira.
El historial (answer, session_question) apunta a estas filas.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime

# --- Lo que dice el markdown (entrada del sync) -------------------------------------


@dataclass(frozen=True)
class OptionSpec:
    text_md: str
    is_correct: bool


@dataclass(frozen=True)
class QuestionSpec:
    key: str
    topic_slug: str
    position: int
    prompt_md: str
    explanation_md: str
    options: tuple[OptionSpec, ...]
    tags: tuple[str, ...]


@dataclass(frozen=True)
class TopicSpec:
    slug: str
    area: str


@dataclass(frozen=True)
class QuizSnapshot:
    topics: tuple[TopicSpec, ...]
    questions: tuple[QuestionSpec, ...]


# --- Lo que hay guardado (id=None: todavía no existe en la DB) ----------------------


@dataclass
class Topic:
    slug: str
    name: str
    area: str
    id: int | None = None


@dataclass
class Option:
    text_md: str
    is_correct: bool
    retired_at: datetime | None = None
    id: int | None = None


@dataclass
class Question:
    key: str
    topic_slug: str
    position: int
    prompt_md: str
    explanation_md: str
    tags: set[str] = field(default_factory=set)
    options: list[Option] = field(default_factory=list)
    retired_at: datetime | None = None
    id: int | None = None


@dataclass
class SyncReport:
    topics_created: int = 0
    topics_updated: int = 0
    questions_created: int = 0
    questions_updated: int = 0
    questions_retired: int = 0
    questions_reactivated: int = 0
    options_created: int = 0
    options_retired: int = 0
    options_reactivated: int = 0

    @property
    def changed(self) -> bool:
        return any(asdict(self).values())


def topic_name(slug: str) -> str:
    """Nombre legible provisional: el markdown no trae uno."""
    return slug.replace("-", " ").title()


class Catalog:
    """Todo lo guardado, indexado por su identidad estable (slug, key)."""

    def __init__(self, topics: list[Topic], questions: list[Question]) -> None:
        self.topics: dict[str, Topic] = {t.slug: t for t in topics}
        self.questions: dict[str, Question] = {q.key: q for q in questions}

    def reconcile(self, snapshot: QuizSnapshot, now: datetime) -> SyncReport:
        """Aplica el markdown sobre lo guardado. Idempotente: la segunda vez no cambia nada."""
        report = SyncReport()

        for spec in snapshot.topics:
            topic = self.topics.get(spec.slug)
            if topic is None:
                self.topics[spec.slug] = Topic(spec.slug, topic_name(spec.slug), spec.area)
                report.topics_created += 1
            elif topic.area != spec.area:
                topic.area = spec.area
                report.topics_updated += 1

        for spec in snapshot.questions:
            question = self.questions.get(spec.key)
            if question is None:
                self.questions[spec.key] = _new_question(spec)
                report.questions_created += 1
                report.options_created += len(spec.options)
            else:
                _update_question(question, spec, now, report)

        wanted = {spec.key for spec in snapshot.questions}
        for key, question in self.questions.items():
            if key not in wanted and question.retired_at is None:
                question.retired_at = now
                report.questions_retired += 1

        return report


def _new_question(spec: QuestionSpec) -> Question:
    return Question(
        key=spec.key,
        topic_slug=spec.topic_slug,
        position=spec.position,
        prompt_md=spec.prompt_md,
        explanation_md=spec.explanation_md,
        tags=set(spec.tags),
        options=[Option(o.text_md, o.is_correct) for o in spec.options],
    )


def _update_question(
    question: Question, spec: QuestionSpec, now: datetime, report: SyncReport
) -> None:
    changed = False
    for attr in ("topic_slug", "position", "prompt_md", "explanation_md"):
        if getattr(question, attr) != getattr(spec, attr):
            setattr(question, attr, getattr(spec, attr))
            changed = True
    if question.tags != set(spec.tags):
        question.tags = set(spec.tags)
        changed = True
    if _reconcile_options(question, spec.options, now, report):
        changed = True

    if question.retired_at is not None:
        question.retired_at = None
        report.questions_reactivated += 1
    elif changed:
        report.questions_updated += 1


def _reconcile_options(
    question: Question, wanted: tuple[OptionSpec, ...], now: datetime, report: SyncReport
) -> bool:
    """La identidad de una opción es su texto dentro de la pregunta.

    Mismo texto: se actualiza is_correct en la misma fila (y se reactiva si estaba retirada).
    Texto nuevo: fila nueva. Texto que ya no está: se retira.
    """
    changed = False
    by_text = {o.text_md: o for o in question.options}

    for spec in wanted:
        option = by_text.get(spec.text_md)
        if option is None:
            question.options.append(Option(spec.text_md, spec.is_correct))
            report.options_created += 1
            changed = True
            continue
        if option.is_correct != spec.is_correct:
            option.is_correct = spec.is_correct
            changed = True
        if option.retired_at is not None:
            option.retired_at = None
            report.options_reactivated += 1
            changed = True

    wanted_texts = {o.text_md for o in wanted}
    for option in question.options:
        if option.text_md not in wanted_texts and option.retired_at is None:
            option.retired_at = now
            report.options_retired += 1
            changed = True

    return changed
