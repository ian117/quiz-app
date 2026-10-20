from __future__ import annotations

from pathlib import Path

import pytest

from app.application.ports import InvalidQuiz
from app.infrastructure.quiz_source import QuizFileSource

BLOCK = """\
## {key}
¿Pregunta?
tags: frecuente

- [x] Correcta
- [ ] Otra uno
- [ ] Otra dos
- [ ] Otra tres

> Explicación: porque sí.
"""


def write(root: Path, category: str, topic: str, *keys: str) -> None:
    path = root / category / f"{topic}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(BLOCK.format(key=k) for k in keys), encoding="utf-8")


def test_traduce_el_markdown_a_snapshot(tmp_path):
    write(tmp_path, "frontend", "react", "react-uno", "react-dos")
    write(tmp_path, "backend", "node", "node-uno")

    snap = QuizFileSource(tmp_path).load()

    assert {(t.slug, t.area) for t in snap.topics} == {("react", "frontend"), ("node", "backend")}
    uno = next(q for q in snap.questions if q.key == "react-uno")
    assert (uno.topic_slug, uno.position, uno.tags) == ("react", 1, ("frecuente",))
    assert [(o.text_md, o.is_correct) for o in uno.options][0] == ("Correcta", True)
    assert next(q for q in snap.questions if q.key == "react-dos").position == 2


def test_quiz_invalido_lanza_invalid_quiz(tmp_path):
    (tmp_path / "frontend").mkdir()
    (tmp_path / "frontend" / "react.md").write_text("## react-roto\nsin opciones\n")

    with pytest.raises(InvalidQuiz, match="react-roto"):
        QuizFileSource(tmp_path).load()


def test_directorio_inexistente(tmp_path):
    with pytest.raises(InvalidQuiz, match="no existe"):
        QuizFileSource(tmp_path / "nada").load()


def test_mismo_tema_en_dos_categorias_se_rechaza(tmp_path):
    write(tmp_path, "frontend", "react", "react-uno")
    write(tmp_path, "fundamentos", "react", "react-dos")

    with pytest.raises(InvalidQuiz, match="dos categorías"):
        QuizFileSource(tmp_path).load()
