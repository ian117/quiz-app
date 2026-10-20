"""Caso de uso: llevar el contenido de quiz/*.md a la base de datos."""
from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from app.application.ports import CatalogRepository, QuizSource
from app.domain.catalog import SyncReport


class SyncQuiz:
    def __init__(
        self,
        source: QuizSource,
        catalog: CatalogRepository,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._source = source
        self._catalog = catalog
        self._clock = clock

    def execute(self) -> SyncReport:
        # Primero el quiz: si es inválido, falla antes de leer o escribir nada en la DB.
        snapshot = self._source.load()
        catalog = self._catalog.load()
        report = catalog.reconcile(snapshot, self._clock())
        if report.changed:
            self._catalog.save(catalog)
        return report
