"""Errores de los casos de uso."""
from __future__ import annotations


class SessionNotFound(Exception):
    def __init__(self, session_id: int) -> None:
        super().__init__(f"no existe la sesión {session_id}")


class EmptySession(Exception):
    def __init__(self) -> None:
        super().__init__("el plan no encontró ninguna pregunta activa")
