"""Sesión de juego: qué preguntas salieron, qué se respondió y cómo se califica."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from app.domain.catalog import Question
from app.domain.errors import AlreadyAnswered, InvalidOption, QuestionNotInSession
from app.domain.selection import Stretch


class Mode(StrEnum):
    TOPIC = "tema"
    RANDOM = "aleatoria"
    SPECIALIZED = "especializada"
    INTERVIEW = "entrevista"
    REAL = "reales"


@dataclass
class Answer:
    question_id: int
    option_id: int
    is_correct: bool
    time_ms: int
    id: int | None = None


@dataclass
class QuizSession:
    mode: Mode
    plan: tuple[Stretch, ...]
    question_ids: tuple[int, ...]  # en el orden en que se juegan
    started_at: datetime
    score: int = 0
    finished_at: datetime | None = None
    answers: list[Answer] = field(default_factory=list)
    id: int | None = None

    @property
    def total(self) -> int:
        return len(self.question_ids)

    @property
    def finished(self) -> bool:
        return self.finished_at is not None

    def answer_for(self, question_id: int) -> Answer | None:
        return next((a for a in self.answers if a.question_id == question_id), None)

    def answer(self, question: Question, option_id: int, time_ms: int, now: datetime) -> Answer:
        """Registra y califica una respuesta. La sesión termina al responder la última."""
        qid = question.id
        if qid is None:
            raise ValueError("la pregunta debe venir de la base de datos")
        if qid not in self.question_ids:
            raise QuestionNotInSession(qid)
        if self.answer_for(qid) is not None:
            raise AlreadyAnswered(qid)
        option = next((o for o in question.options if o.id == option_id), None)
        if option is None:
            raise InvalidOption(qid, option_id)

        answer = Answer(qid, option_id, option.is_correct, time_ms)
        self.answers.append(answer)
        if answer.is_correct:
            self.score += 1
        if len(self.answers) == self.total:
            self.finished_at = now
        return answer
