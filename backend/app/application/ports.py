"""Puertos: lo que los casos de uso necesitan del exterior."""
from __future__ import annotations

from typing import Protocol

from app.domain.catalog import Catalog, QuizSnapshot


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
