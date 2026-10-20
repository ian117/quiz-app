"""Entrada por línea de comandos: python -m app.cli.sync

Variables: DATABASE_URL y QUIZ_DIR (en Docker, /quiz montado :ro).
Códigos de salida: 0 bien, 1 quiz inválido, 2 configuración incompleta.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.application.ports import InvalidQuiz
from app.application.sync_quiz import SyncQuiz
from app.infrastructure.catalog_repository import SqlAlchemyCatalogRepository
from app.infrastructure.quiz_source import QuizFileSource


def main() -> int:
    database_url, quiz_dir = os.environ.get("DATABASE_URL"), os.environ.get("QUIZ_DIR")
    if not database_url or not quiz_dir:
        print("Faltan las variables DATABASE_URL y QUIZ_DIR", file=sys.stderr)
        return 2

    engine = create_engine(database_url)
    try:
        # Una sola transacción: o entra todo el quiz o no entra nada.
        with Session(engine) as session, session.begin():
            source = QuizFileSource(Path(quiz_dir))
            report = SyncQuiz(source, SqlAlchemyCatalogRepository(session)).execute()
    except InvalidQuiz as exc:
        print(f"{exc}\nLa base de datos no se tocó.", file=sys.stderr)
        return 1
    finally:
        engine.dispose()

    print("sync: " + (", ".join(f"{k}={v}" for k, v in vars(report).items() if v) or "sin cambios"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
