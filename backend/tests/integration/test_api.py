"""La API completa (HTTP -> casos de uso -> Postgres real), con datos que carga el sync."""
from __future__ import annotations

from collections.abc import Iterator
from random import Random

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.api.main import create_app

from .helpers import Quiz, block

pytestmark = pytest.mark.integration


@pytest.fixture
def seeded(quiz: Quiz) -> Quiz:
    quiz.write(
        "frontend",
        "react",
        block("react-uno", "frecuente, hooks"),
        block("react-dos", "hooks"),
        block("react-tres", "frecuente"),
    )
    quiz.write("backend", "node", block("node-uno", "senior"), block("node-dos"))
    assert quiz.sync() == 0
    return quiz


@pytest.fixture
def client(engine: Engine, seeded: Quiz) -> Iterator[TestClient]:
    with TestClient(create_app(engine, lambda: Random(0))) as c:
        yield c


def plan(**stretch) -> dict:
    return {"mode": "tema", "plan": [stretch]}


def start(client: TestClient, **stretch) -> dict:
    response = client.post("/sessions", json=plan(**stretch))
    assert response.status_code == 201, response.text
    return response.json()


def correct_option(engine: Engine, question_id: int) -> int:
    with engine.connect() as conn:
        return conn.scalar(
            text("SELECT id FROM option WHERE question_id = :q AND is_correct"), {"q": question_id}
        )


def count(engine: Engine, table: str) -> int:
    with engine.connect() as conn:
        return conn.scalar(text(f'SELECT count(*) FROM "{table}"'))


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


class TestCatalogo:
    def test_conteos_de_preguntas_activas(self, client):
        data = client.get("/catalog").json()

        assert data["areas"] == [
            {"slug": "backend", "question_count": 2},
            {"slug": "frontend", "question_count": 3},
        ]
        assert {t["slug"]: t["question_count"] for t in data["topics"]} == {"node": 2, "react": 3}
        assert {t["slug"]: t["question_count"] for t in data["tags"]} == {
            "frecuente": 2, "hooks": 2, "senior": 1,
        }  # fmt: skip

    def test_las_retiradas_no_cuentan(self, client, seeded):
        seeded.write("frontend", "react", block("react-uno", "frecuente, hooks"))
        seeded.sync()

        data = client.get("/catalog").json()

        assert {t["slug"]: t["question_count"] for t in data["topics"]}["react"] == 1
        assert {t["slug"]: t["question_count"] for t in data["tags"]}["frecuente"] == 1


class TestCrearSesion:
    def test_devuelve_las_preguntas_del_plan(self, client, engine):
        session = start(client, topic="react")

        assert session["total"] == 3 and session["answered"] == 0 and session["mode"] == "tema"
        assert {q["key"] for q in session["questions"]} == {"react-uno", "react-dos", "react-tres"}
        assert [q["position"] for q in session["questions"]] == [1, 2, 3]
        assert session["plan"][0]["topic"] == "react" and session["plan"][0]["order"] == "random"
        assert count(engine, "session_question") == 3

    def test_nunca_revela_la_correcta_ni_la_explicacion(self, client):
        body = client.post("/sessions", json=plan(area="frontend")).text

        for forbidden in ("is_correct", "correct_option_id", "explanation_md", "Porque sí"):
            assert forbidden not in body

    def test_modos_y_tramos_de_vision(self, client):
        phases = {
            "mode": "entrevista",
            "plan": [
                {"tags": ["frecuente"], "n": 1},
                {"area": "backend", "n": 1},
                {"topics": ["react"], "n": 1, "order": "en-orden"},
            ],
        }

        session = client.post("/sessions", json=phases).json()

        assert session["total"] == 3 and session["mode"] == "entrevista"
        assert len({q["id"] for q in session["questions"]}) == 3

    def test_n_limita_y_en_orden_respeta_el_archivo(self, client):
        session = start(client, topic="react", n=2, order="en-orden")

        assert [q["key"] for q in session["questions"]] == ["react-uno", "react-dos"]

    @pytest.mark.parametrize(
        "body",
        [
            {"mode": "tema", "plan": []},
            {"mode": "inventado", "plan": [{"topic": "react"}]},
            {"mode": "tema", "plan": [{"topic": "react", "n": 0}]},
            {"mode": "tema", "plan": [{"topic": "react", "order": "al-azar"}]},
            {"mode": "tema", "plan": [{"topic": "react", "dificultad": "alta"}]},
            {"plan": [{"topic": "react"}]},
        ],
    )
    def test_plan_invalido(self, client, body):
        assert client.post("/sessions", json=body).status_code == 422

    def test_plan_sin_preguntas(self, client, engine):
        response = client.post("/sessions", json=plan(topic="rust"))

        assert response.status_code == 422
        assert "ninguna pregunta" in response.json()["detail"]
        assert count(engine, "session") == 0


class TestResponder:
    def test_califica_y_revela_la_correcta_con_la_explicacion(self, client, engine):
        session = start(client, topic="react")
        q = session["questions"][0]
        right = correct_option(engine, q["id"])
        wrong = next(o["id"] for o in q["options"] if o["id"] != right)

        result = client.post(
            f"/sessions/{session['id']}/answers",
            json={"question_id": q["id"], "option_id": wrong, "time_ms": 1200},
        ).json()

        assert result["answer"]["is_correct"] is False
        assert result["answer"]["correct_option_id"] == right
        assert result["answer"]["explanation_md"] == "porque sí."
        assert (result["score"], result["answered"], result["total"]) == (0, 1, 3)
        assert result["finished"] is False
        assert count(engine, "answer") == 1

    def test_sesion_completa(self, client, engine):
        session = start(client, topic="react")

        for q in session["questions"]:
            result = client.post(
                f"/sessions/{session['id']}/answers",
                json={
                    "question_id": q["id"],
                    "option_id": correct_option(engine, q["id"]),
                    "time_ms": 500,
                },
            ).json()

        assert (result["score"], result["answered"], result["finished"]) == (3, 3, True)
        final = client.get(f"/sessions/{session['id']}").json()
        assert final["finished_at"] is not None and final["score"] == 3

    def test_no_se_responde_dos_veces(self, client, engine):
        session = start(client, topic="react")
        q = session["questions"][0]
        body = {"question_id": q["id"], "option_id": q["options"][0]["id"], "time_ms": 1}
        url = f"/sessions/{session['id']}/answers"
        assert client.post(url, json=body).status_code == 200

        again = client.post(url, json=body)

        assert again.status_code == 409
        assert count(engine, "answer") == 1

    def test_sesion_inexistente(self, client):
        body = {"question_id": 1, "option_id": 1, "time_ms": 1}

        assert client.post("/sessions/999/answers", json=body).status_code == 404
        assert client.get("/sessions/999").status_code == 404

    def test_pregunta_que_no_salio_en_la_sesion(self, client, engine):
        session = start(client, topic="react")
        node = start(client, topic="node")["questions"][0]

        response = client.post(
            f"/sessions/{session['id']}/answers",
            json={"question_id": node["id"], "option_id": node["options"][0]["id"], "time_ms": 1},
        )

        assert response.status_code == 422
        assert count(engine, "answer") == 0

    def test_opcion_de_otra_pregunta(self, client, engine):
        session = start(client, topic="react")
        first, second = session["questions"][:2]

        response = client.post(
            f"/sessions/{session['id']}/answers",
            json={
                "question_id": first["id"],
                "option_id": second["options"][0]["id"],
                "time_ms": 1,
            },
        )

        assert response.status_code == 422
        assert count(engine, "answer") == 0

    def test_tiempo_negativo(self, client):
        session = start(client, topic="react")
        q = session["questions"][0]

        response = client.post(
            f"/sessions/{session['id']}/answers",
            json={"question_id": q["id"], "option_id": q["options"][0]["id"], "time_ms": -1},
        )

        assert response.status_code == 422


class TestHistorial:
    def test_get_muestra_el_mismo_orden_de_opciones(self, client):
        session = start(client, area="frontend")

        for _ in range(3):
            again = client.get(f"/sessions/{session['id']}").json()
            assert [[o["id"] for o in q["options"]] for q in again["questions"]] == [
                [o["id"] for o in q["options"]] for q in session["questions"]
            ]

    def test_la_correcta_no_queda_siempre_arriba(self, client, engine):
        # En el markdown la correcta va primero (id más bajo); el servidor la reparte.
        firsts = []
        for _ in range(30):
            for q in start(client, topic="react")["questions"]:
                firsts.append(q["options"][0]["id"] == correct_option(engine, q["id"]))

        assert 0.10 < sum(firsts) / len(firsts) < 0.45  # lo esperado es 25%

    def test_get_no_revela_lo_que_no_se_respondio(self, client, engine):
        session = start(client, topic="react")
        q = session["questions"][0]
        client.post(
            f"/sessions/{session['id']}/answers",
            json={
                "question_id": q["id"],
                "option_id": correct_option(engine, q["id"]),
                "time_ms": 1,
            },
        )

        data = client.get(f"/sessions/{session['id']}").json()

        assert data["questions"][0]["answer"]["is_correct"] is True
        assert all(other["answer"] is None for other in data["questions"][1:])
        assert data["questions"][1:] and "explanation_md" not in str(data["questions"][1:])

    def test_listado_de_la_mas_reciente_a_la_mas_antigua(self, client):
        first = start(client, topic="react")
        second = start(client, topic="node")

        listed = client.get("/sessions").json()

        assert [s["id"] for s in listed] == [second["id"], first["id"]]
        assert listed[0] == {
            "id": second["id"], "mode": "tema", "started_at": listed[0]["started_at"],
            "finished_at": None, "score": 0, "total": 2, "answered": 0,
        }  # fmt: skip
        assert [s["id"] for s in client.get("/sessions?limit=1&offset=1").json()] == [first["id"]]

    def test_retirar_una_pregunta_no_rompe_el_historial(self, client, engine, seeded):
        session = start(client, topic="react")
        q = next(q for q in session["questions"] if q["key"] == "react-dos")
        client.post(
            f"/sessions/{session['id']}/answers",
            json={"question_id": q["id"], "option_id": q["options"][0]["id"], "time_ms": 1},
        )

        seeded.write("frontend", "react", block("react-uno", "frecuente, hooks"))
        seeded.sync()

        again = client.get(f"/sessions/{session['id']}").json()
        assert {x["key"] for x in again["questions"]} == {"react-uno", "react-dos", "react-tres"}
        assert next(x for x in again["questions"] if x["key"] == "react-dos")["answer"]
        assert start(client, topic="react")["total"] == 1  # las nuevas ya no la incluyen

    def test_opcion_editada_conserva_lo_respondido(self, client, engine, seeded):
        session = start(client, topic="react", n=1, order="en-orden")
        q = session["questions"][0]
        old = q["options"][0]
        client.post(
            f"/sessions/{session['id']}/answers",
            json={"question_id": q["id"], "option_id": old["id"], "time_ms": 1},
        )

        seeded.write(
            "frontend",
            "react",
            block("react-uno", "frecuente, hooks", options=("A", "B", "C", "D otra")),
            block("react-dos", "hooks"),
            block("react-tres", "frecuente"),
        )
        seeded.sync()
        again = client.get(f"/sessions/{session['id']}").json()["questions"][0]

        assert again["answer"]["option_id"] == old["id"]
        assert old["id"] in {o["id"] for o in again["options"]}


def test_cors_solo_para_el_frontend_local(client):
    ok = client.options(
        "/sessions",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"},
    )
    other = client.options(
        "/sessions",
        headers={"Origin": "http://malo.example", "Access-Control-Request-Method": "POST"},
    )

    assert ok.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "access-control-allow-origin" not in other.headers
