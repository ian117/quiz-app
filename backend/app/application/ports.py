"""Puertos: lo que los casos de uso necesitan del exterior."""
from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from app.application.views import CatalogView
from app.domain.catalog import Catalog, Question, QuizSnapshot
from app.domain.selection import Candidate
from app.domain.session import QuizSession


class InvalidQuiz(Exception):
    """El quiz no cumple la convención. Lleva la lista de problemas en el mensaje."""


class QuizSource(Protocol):
    def load(self) -> QuizSnapshot:
        """Lee y valida el quiz completo. Lanza InvalidQuiz si hay algún error."""
        ...


class CatalogRepository(Protocol):
    def load(self) -> Catalog:
        """Todo lo guardado, retirado incluido."""
        ...

    def save(self, catalog: Catalog) -> None:
        """Persiste el catálogo. La transacción la controla quien llama."""
        ...


class QuestionReader(Protocol):
    def candidates(self) -> list[Candidate]:
        """Las preguntas activas, con lo justo para filtrarlas."""
        ...

    def get_many(self, question_ids: Sequence[int]) -> dict[int, Question]:
        """Preguntas con todas sus opciones (retiradas incluidas), por id."""
        ...

    def catalog(self) -> CatalogView:
        """Áreas, temas y tags con cuántas preguntas activas tiene cada uno."""
        ...


class SessionRepository(Protocol):
    def add(self, session: QuizSession) -> None:
        """Guarda una sesión nueva con sus preguntas y le asigna el id."""
        ...

    def get(self, session_id: int) -> QuizSession | None: ...

    def save(self, session: QuizSession) -> None:
        """Guarda lo que cambió: respuestas nuevas, puntaje y cierre."""
        ...

    def list_recent(self, limit: int, offset: int) -> list[QuizSession]:
        """De la más reciente a la más antigua."""
        ...
