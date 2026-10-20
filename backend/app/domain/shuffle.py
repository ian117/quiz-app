"""Orden en que se muestran las opciones de una pregunta dentro de una sesión.

El markdown pone la correcta primero y `option` no guarda orden, así que el orden se deriva:
es una función pura de (session_id, question_id) y de la identidad de cada opción. Pedir
la misma sesión dos veces muestra lo mismo sin guardar nada.

No se usa `random` ni `hash()`: el primero no garantiza el mismo barajado entre versiones de
Python y el segundo cambia en cada proceso. Cambiar este algoritmo reordena el historial.
"""
from __future__ import annotations

import hashlib
from collections.abc import Sequence


def shuffle_option_ids(option_ids: Sequence[int], session_id: int, question_id: int) -> list[int]:
    """Las mismas opciones en un orden estable para esta sesión y pregunta.

    Cada opción se ordena por el hash de (sesión, pregunta, opción). Por eso el resultado
    no depende del orden de entrada, y retirar una opción no mueve la posición relativa
    de las demás.
    """

    def sort_key(option_id: int) -> tuple[bytes, int]:
        digest = hashlib.sha256(f"{session_id}:{question_id}:{option_id}".encode()).digest()
        return digest, option_id

    return sorted(option_ids, key=sort_key)
