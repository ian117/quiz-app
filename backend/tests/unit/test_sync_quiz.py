from __future__ import annotations

import pytest

from app.application.ports import InvalidQuiz
from app.application.sync_quiz import SyncQuiz

from .builders import T0, InMemoryCatalogRepository, StaticQuizSource, question, snapshot


def use_case(source, repo) -> SyncQuiz:
    return SyncQuiz(source, repo, clock=lambda: T0)


def test_guarda_el_catalogo():
    repo = InMemoryCatalogRepository()

    report = use_case(StaticQuizSource(snapshot(question())), repo).execute()

    assert report.questions_created == 1
    assert "react-uno" in repo.stored.questions


def test_quiz_invalido_falla_sin_tocar_el_repositorio():
    repo = InMemoryCatalogRepository()

    with pytest.raises(InvalidQuiz):
        use_case(StaticQuizSource(InvalidQuiz("roto")), repo).execute()

    assert (repo.loads, repo.saves) == (0, 0)


def test_sin_cambios_no_vuelve_a_guardar():
    repo = InMemoryCatalogRepository()
    source = StaticQuizSource(snapshot(question()))

    use_case(source, repo).execute()
    report = use_case(source, repo).execute()

    assert not report.changed
    assert repo.saves == 1
