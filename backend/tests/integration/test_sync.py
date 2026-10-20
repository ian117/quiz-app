"""El sync completo (markdown real -> CLI -> Postgres real)."""
from __future__ import annotations

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.cli.sync import main
from app.infrastructure.orm.models import Base

from .helpers import Quiz, block

pytestmark = pytest.mark.integration

TABLES = [t.name for t in Base.metadata.sorted_tables]


def dump(engine: Engine) -> dict[str, list]:
    with engine.connect() as conn:
        return {t: conn.execute(text(f'SELECT * FROM "{t}" ORDER BY 1, 2')).all() for t in TABLES}


def scalar(engine: Engine, sql: str, **params):
    with engine.connect() as conn:
        return conn.scalar(text(sql), params)


def rows(engine: Engine, sql: str, **params) -> list:
    with engine.connect() as conn:
        return conn.execute(text(sql), params).all()


def record_history(engine: Engine, question_key: str, option_text: str) -> None:
    """Una sesión con una respuesta, como la dejaría la api."""
    with engine.begin() as conn:
        qid = conn.scalar(text("SELECT id FROM question WHERE key = :k"), {"k": question_key})
        oid = conn.scalar(
            text("SELECT id FROM option WHERE question_id = :q AND text_md = :t"),
            {"q": qid, "t": option_text},
        )
        sid = conn.scalar(
            text("INSERT INTO session (mode, plan, total) VALUES ('tema', '[]', 1) RETURNING id")
        )
        conn.execute(
            text("INSERT INTO session_question VALUES (:s, :q, 1)"), {"s": sid, "q": qid}
        )
        conn.execute(
            text("INSERT INTO answer (session_id, question_id, option_id, is_correct, time_ms)"
                 " VALUES (:s, :q, :o, false, 1200)"),
            {"s": sid, "q": qid, "o": oid},
        )  # fmt: skip


def test_primera_carga(quiz: Quiz, engine: Engine):
    quiz.write("frontend", "react", block("react-uno", "frecuente, hooks"), block("react-dos"))

    assert quiz.sync() == 0

    assert rows(engine, "SELECT slug, name, area FROM topic") == [("react", "React", "frontend")]
    assert rows(engine, "SELECT key, position FROM question ORDER BY position") == [
        ("react-uno", 1), ("react-dos", 2),
    ]  # fmt: skip
    assert scalar(engine, "SELECT count(*) FROM option") == 8
    assert scalar(engine, "SELECT count(*) FROM option WHERE is_correct") == 2
    assert rows(
        engine,
        "SELECT t.slug FROM question_tag qt JOIN tag t ON t.id = qt.tag_id ORDER BY t.slug",
    ) == [("frecuente",), ("hooks",)]


def test_es_idempotente(quiz: Quiz, engine: Engine, capsys):
    quiz.write("frontend", "react", block("react-uno", "frecuente"), block("react-dos"))
    quiz.write("backend", "node", block("node-uno", "senior"))
    quiz.sync()
    before = dump(engine)
    capsys.readouterr()

    assert quiz.sync() == 0

    assert dump(engine) == before
    assert "sin cambios" in capsys.readouterr().out


def test_retira_sin_borrar_y_reactiva_con_el_mismo_id(quiz: Quiz, engine: Engine):
    quiz.write("frontend", "react", block("react-uno"), block("react-dos"))
    quiz.sync()
    dos_id = scalar(engine, "SELECT id FROM question WHERE key = 'react-dos'")

    quiz.write("frontend", "react", block("react-uno"))
    quiz.sync()
    assert scalar(engine, "SELECT retired_at FROM question WHERE key = 'react-dos'") is not None
    assert scalar(engine, "SELECT count(*) FROM question") == 2

    quiz.write("frontend", "react", block("react-uno"), block("react-dos"))
    quiz.sync()
    assert scalar(engine, "SELECT retired_at FROM question WHERE key = 'react-dos'") is None
    assert scalar(engine, "SELECT id FROM question WHERE key = 'react-dos'") == dos_id


def test_insertar_en_medio_conserva_ids_y_recalcula_position(quiz: Quiz, engine: Engine):
    quiz.write("frontend", "react", block("react-a"), block("react-b"))
    quiz.sync()
    b_id = scalar(engine, "SELECT id FROM question WHERE key = 'react-b'")

    quiz.write("frontend", "react", block("react-a"), block("react-nueva"), block("react-b"))
    quiz.sync()

    assert rows(engine, "SELECT key, position FROM question ORDER BY position") == [
        ("react-a", 1), ("react-nueva", 2), ("react-b", 3),
    ]  # fmt: skip
    assert scalar(engine, "SELECT id FROM question WHERE key = 'react-b'") == b_id


def test_quiz_invalido_no_toca_la_db(quiz: Quiz, engine: Engine, capsys):
    quiz.write("frontend", "react", block("react-uno"))
    quiz.sync()
    before = dump(engine)

    quiz.write("frontend", "react", block("react-uno"), "## react-roto\nsin opciones\n")

    assert quiz.sync() == 1
    assert dump(engine) == before
    assert "react-roto" in capsys.readouterr().err


def test_sin_variables_termina_con_2(monkeypatch, capsys):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("QUIZ_DIR", raising=False)

    assert main() == 2


def test_cambiar_tags_actualiza_question_tag(quiz: Quiz, engine: Engine):
    quiz.write("frontend", "react", block("react-uno", "frecuente, hooks"))
    quiz.sync()

    quiz.write("frontend", "react", block("react-uno", "senior"))
    quiz.sync()

    assert rows(
        engine,
        "SELECT t.slug FROM question_tag qt JOIN tag t ON t.id = qt.tag_id ORDER BY t.slug",
    ) == [("senior",)]
    # Los tags son vocabulario compartido: no se borran aunque ninguna pregunta los use.
    assert scalar(engine, "SELECT count(*) FROM tag") == 3


class TestOpcionesConHistorial:
    def test_cambiar_cual_es_la_correcta_actualiza_la_misma_fila(self, quiz: Quiz, engine: Engine):
        quiz.write("frontend", "react", block("react-uno", options=("A", "B", "C", "D")))
        quiz.sync()
        ids = dict(rows(engine, "SELECT text_md, id FROM option"))

        quiz.write("frontend", "react", block("react-uno", options=("B", "A", "C", "D")))
        quiz.sync()

        assert dict(rows(engine, "SELECT text_md, id FROM option")) == ids
        assert rows(engine, "SELECT text_md FROM option WHERE is_correct") == [("B",)]

    def test_editar_el_texto_retira_la_vieja_y_el_historial_sigue_intacto(
        self, quiz: Quiz, engine: Engine
    ):
        quiz.write("frontend", "react", block("react-uno", options=("A", "B", "C", "D")))
        quiz.sync()
        record_history(engine, "react-uno", "B")

        quiz.write("frontend", "react", block("react-uno", options=("A", "B nueva", "C", "D")))
        quiz.sync()

        assert scalar(engine, "SELECT retired_at FROM option WHERE text_md = 'B'") is not None
        assert scalar(engine, "SELECT retired_at FROM option WHERE text_md = 'B nueva'") is None
        # La respuesta del historial sigue apuntando a la opción retirada, con su texto original.
        assert rows(
            engine, "SELECT o.text_md FROM answer a JOIN option o ON o.id = a.option_id"
        ) == [("B",)]

    def test_texto_que_vuelve_se_reactiva_sin_duplicar(self, quiz: Quiz, engine: Engine):
        quiz.write("frontend", "react", block("react-uno", options=("A", "B", "C", "D")))
        quiz.sync()
        b_id = scalar(engine, "SELECT id FROM option WHERE text_md = 'B'")
        quiz.write("frontend", "react", block("react-uno", options=("A", "B nueva", "C", "D")))
        quiz.sync()

        quiz.write("frontend", "react", block("react-uno", options=("A", "B", "C", "D")))
        quiz.sync()

        assert scalar(engine, "SELECT count(*) FROM option") == 5
        assert scalar(engine, "SELECT retired_at FROM option WHERE id = :i", i=b_id) is None
        assert scalar(engine, "SELECT retired_at FROM option WHERE text_md = 'B nueva'") is not None


def test_las_migraciones_coinciden_con_los_modelos(engine: Engine):
    with engine.connect() as conn:
        diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)

    assert diff == []
