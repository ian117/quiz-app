from __future__ import annotations

from dataclasses import asdict
from random import Random

import pytest

from app.application.errors import EmptySession, SessionNotFound
from app.application.sessions import AnswerQuestion, CreateSession, GetSession, ListSessions
from app.domain.catalog import Option, Question
from app.domain.errors import AlreadyAnswered, QuestionNotInSession
from app.domain.selection import Stretch
from app.domain.session import Mode

from .builders import T0, T1, InMemoryQuestionReader, InMemorySessionRepository


def stored(qid: int, topic: str = "react", tags: set[str] | None = None) -> Question:
    base = qid * 10
    return Question(
        key=f"{topic}-{qid}",
        topic_slug=topic,
        position=qid,
        prompt_md=f"¿Pregunta {qid}?",
        explanation_md=f"Explicación {qid}.",
        tags=tags or set(),
        options=[
            Option("correcta", True, id=base + 1),
            Option("B", False, id=base + 2),
            Option("C", False, id=base + 3),
            Option("D", False, id=base + 4),
        ],
        id=qid,
    )


@pytest.fixture
def reader() -> InMemoryQuestionReader:
    return InMemoryQuestionReader(stored(1), stored(2), stored(3, "node"))


@pytest.fixture
def sessions() -> InMemorySessionRepository:
    return InMemorySessionRepository()


REACT = (Stretch(topic="react"),)


def create(reader, sessions, plan=REACT, mode=Mode.TOPIC):
    return CreateSession(reader, sessions, lambda: Random(0), lambda: T0).execute(mode, plan)


def option_ids(view) -> dict[int, list[int]]:
    return {q.id: [o.id for o in q.options] for q in view.questions}


class TestCreateSession:
    def test_elige_guarda_y_devuelve_las_preguntas(self, reader, sessions):
        view = create(reader, sessions)

        assert view.id == 1 and view.total == 2 and view.answered == 0
        assert {q.key for q in view.questions} == {"react-1", "react-2"}
        assert sessions.sessions[1].question_ids == tuple(q.id for q in view.questions)

    def test_no_revela_ninguna_respuesta(self, reader, sessions):
        view = create(reader, sessions)

        assert all(q.answer is None for q in view.questions)
        text = repr(view)
        assert "is_correct" not in text and "Explicación" not in text

    def test_las_opciones_salen_barajadas_y_estables(self, reader, sessions):
        view = create(reader, sessions)
        again = GetSession(reader, sessions).execute(view.id)

        assert [q.options for q in view.questions] == [q.options for q in again.questions]

    def test_sin_preguntas_es_un_error(self, reader, sessions):
        with pytest.raises(EmptySession):
            create(reader, sessions, (Stretch(topic="rust"),))
        assert sessions.sessions == {}

    def test_ignora_las_retiradas(self, sessions):
        retired = stored(2)
        retired.retired_at = T0
        view = create(InMemoryQuestionReader(stored(1), retired), sessions)

        assert [q.key for q in view.questions] == ["react-1"]


class TestAnswerQuestion:
    def answer(self, reader, sessions, **kw):
        args = {"session_id": 1, "question_id": 1, "option_id": 11, "time_ms": 900} | kw
        return AnswerQuestion(reader, sessions, lambda: T1).execute(**args)

    def test_califica_y_revela_la_correcta_con_la_explicacion(self, reader, sessions):
        create(reader, sessions)

        result = self.answer(reader, sessions, option_id=12)

        assert not result.answer.is_correct
        assert result.answer.correct_option_id == 11
        assert result.answer.explanation_md == "Explicación 1."
        assert (result.score, result.answered, result.total, result.finished) == (0, 1, 2, False)

    def test_cierra_la_sesion_con_la_ultima(self, reader, sessions):
        create(reader, sessions)
        self.answer(reader, sessions)

        result = self.answer(reader, sessions, question_id=2, option_id=21)

        assert (result.score, result.finished) == (2, True)
        assert sessions.sessions[1].finished_at == T1

    def test_responder_dos_veces(self, reader, sessions):
        create(reader, sessions)
        self.answer(reader, sessions)

        with pytest.raises(AlreadyAnswered):
            self.answer(reader, sessions)

    def test_sesion_inexistente(self, reader, sessions):
        with pytest.raises(SessionNotFound):
            self.answer(reader, sessions, session_id=99)

    def test_pregunta_de_otra_sesion(self, reader, sessions):
        create(reader, sessions)

        with pytest.raises(QuestionNotInSession):
            self.answer(reader, sessions, question_id=3, option_id=31)


class TestGetSession:
    def test_lo_respondido_muestra_la_correcta_y_lo_demas_no(self, reader, sessions):
        create(reader, sessions)
        AnswerQuestion(reader, sessions, lambda: T1).execute(1, 1, 12, 500)

        view = GetSession(reader, sessions).execute(1)
        by_id = {q.id: q for q in view.questions}

        assert by_id[1].answer is not None and by_id[1].answer.correct_option_id == 11
        assert by_id[2].answer is None
        assert "is_correct" not in repr(by_id[2])

    def test_opcion_retirada_se_muestra_solo_si_se_respondio(self, reader, sessions):
        create(reader, sessions)
        AnswerQuestion(reader, sessions, lambda: T1).execute(1, 1, 12, 500)
        for q in (reader.questions[1], reader.questions[2]):
            q.options[1].retired_at = T1  # la opción B de cada pregunta

        view = GetSession(reader, sessions).execute(1)
        by_id = {q.id: q for q in view.questions}

        assert 12 in {o.id for o in by_id[1].options}  # la respondida se conserva
        assert 22 not in {o.id for o in by_id[2].options}  # la no respondida ya no sale

    def test_retirar_una_opcion_no_reordena_las_demas(self, reader, sessions):
        create(reader, sessions)
        before = option_ids(GetSession(reader, sessions).execute(1))

        reader.questions[1].options[2].retired_at = T1
        after = option_ids(GetSession(reader, sessions).execute(1))

        assert after[1] == [i for i in before[1] if i != 13]
        assert after[2] == before[2]

    def test_inexistente(self, reader, sessions):
        with pytest.raises(SessionNotFound):
            GetSession(reader, sessions).execute(5)


def test_historial_de_la_mas_reciente_a_la_mas_antigua(reader, sessions):
    create(reader, sessions)
    create(reader, sessions, (Stretch(topic="node"),), Mode.RANDOM)

    summaries = ListSessions(sessions).execute()

    assert [(s.id, s.mode, s.total) for s in summaries] == [(2, Mode.RANDOM, 1), (1, Mode.TOPIC, 2)]
    assert "questions" not in asdict(summaries[0])
