"""Plan de una sesión (tramos) y la regla que elige las preguntas.

Un tramo es {filtro, n, orden}. Dentro de un tramo, las claves del filtro se combinan con AND
y los valores de una lista con OR: `{area: backend, tags: [a, b]}` es "backend Y (a O b)".
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from random import Random

FREQUENT_TAG = "frecuente"


class Order(StrEnum):
    RANDOM = "random"
    IN_ORDER = "en-orden"
    FREQUENT_FIRST = "frecuentes-primero"


@dataclass(frozen=True)
class Candidate:
    """Una pregunta activa, con lo justo para filtrarla."""

    question_id: int
    topic_slug: str
    area: str
    position: int
    tags: frozenset[str]


@dataclass(frozen=True)
class Stretch:
    """Un tramo del plan. `n=None` significa todas las que cumplan el filtro."""

    n: int | None = None
    order: Order = Order.RANDOM
    topic: str | None = None
    topics: tuple[str, ...] = ()
    area: str | None = None
    tags: tuple[str, ...] = ()

    def matches(self, c: Candidate) -> bool:
        return (
            (self.topic is None or c.topic_slug == self.topic)
            and (not self.topics or c.topic_slug in self.topics)
            and (self.area is None or c.area == self.area)
            and (not self.tags or not c.tags.isdisjoint(self.tags))
        )


def select_questions(
    candidates: Sequence[Candidate], plan: Sequence[Stretch], rng: Random
) -> list[int]:
    """Los ids de las preguntas de la sesión, en el orden en que se jugarán.

    Una pregunta no se repite entre tramos: cada tramo excluye lo que ya salió. Si un tramo
    tiene menos preguntas de las pedidas, aporta las que haya.
    """
    chosen: list[int] = []
    taken: set[int] = set()
    for stretch in plan:
        pool = [c for c in candidates if c.question_id not in taken and stretch.matches(c)]
        ordered = _order(pool, stretch.order, rng)
        picked = ordered if stretch.n is None else ordered[: stretch.n]
        chosen += [c.question_id for c in picked]
        taken.update(c.question_id for c in picked)
    return chosen


def _order(pool: list[Candidate], order: Order, rng: Random) -> list[Candidate]:
    if order is Order.IN_ORDER:
        return sorted(pool, key=lambda c: (c.topic_slug, c.position, c.question_id))
    if order is Order.FREQUENT_FIRST:
        frequent = [c for c in pool if FREQUENT_TAG in c.tags]
        rest = [c for c in pool if FREQUENT_TAG not in c.tags]
        rng.shuffle(frequent)
        rng.shuffle(rest)
        return frequent + rest
    shuffled = list(pool)
    rng.shuffle(shuffled)
    return shuffled
