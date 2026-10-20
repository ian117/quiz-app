"""Errores de las reglas del juego."""
from __future__ import annotations


class DomainError(Exception):
    """Base: una regla del dominio no se cumple."""


class QuestionNotInSession(DomainError):
    def __init__(self, question_id: int) -> None:
        super().__init__(f"la pregunta {question_id} no salió en esta sesión")


class InvalidOption(DomainError):
    def __init__(self, question_id: int, option_id: int) -> None:
        super().__init__(f"la opción {option_id} no pertenece a la pregunta {question_id}")


class AlreadyAnswered(DomainError):
    def __init__(self, question_id: int) -> None:
        super().__init__(f"la pregunta {question_id} ya se respondió en esta sesión")
