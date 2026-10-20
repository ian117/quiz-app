from __future__ import annotations

import pytest

from app.domain.catalog import Option, Question
from app.domain.errors import AlreadyAnswered, InvalidOption, QuestionNotInSession
from app.domain.selection import Stretch
from app.domain.session import Mode, QuizSession

from .builders import T0, T1


def question(qid: int, first_option_id: int) -> Question:
    return Question(
        key=f"react-{qid}",
        topic_slug="react",
        position=qid,
        prompt_md="¿?",
        explanation_md="Porque sí.",
        options=[
            Option("A", True, id=first_option_id),
            Option("B", False, id=first_option_id + 1),
            Option("C", False, id=first_option_id + 2),
        ],
        id=qid,
    )


@pytest.fixture
def session() -> QuizSession:
    return QuizSession(Mode.TOPIC, (Stretch(topic="react"),), (1, 2), started_at=T0, id=9)


def test_acierto_suma_al_puntaje(session):
    answer = session.answer(question(1, 10), 10, 1500, T1)

    assert answer.is_correct and answer.time_ms == 1500
    assert session.score == 1


def test_fallo_no_suma(session):
    answer = session.answer(question(1, 10), 11, 800, T1)

    assert not answer.is_correct
    assert session.score == 0


def test_termina_al_responder_la_ultima(session):
    session.answer(question(1, 10), 10, 1, T0)
    assert not session.finished

    session.answer(question(2, 20), 21, 1, T1)

    assert session.finished_at == T1
    assert (session.score, session.total) == (1, 2)


def test_no_se_responde_dos_veces(session):
    session.answer(question(1, 10), 10, 1, T0)

    with pytest.raises(AlreadyAnswered):
        session.answer(question(1, 10), 11, 1, T1)
    assert session.score == 1


def test_pregunta_que_no_salio_en_la_sesion(session):
    with pytest.raises(QuestionNotInSession):
        session.answer(question(3, 30), 30, 1, T0)


def test_opcion_de_otra_pregunta(session):
    with pytest.raises(InvalidOption):
        session.answer(question(1, 10), 20, 1, T0)
    assert session.answers == []
