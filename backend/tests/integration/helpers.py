"""Ayudas de los tests de integración: un quiz/ de prueba y bloques markdown válidos."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.cli.sync import main


def block(key: str, tags: str = "", options: tuple[str, ...] = ("A", "B", "C", "D")) -> str:
    correct, *wrong = options
    tags_line = f"tags: {tags}\n" if tags else ""
    items = "\n".join([f"- [x] {correct}", *(f"- [ ] {w}" for w in wrong)])
    return f"## {key}\n¿Pregunta {key}?\n{tags_line}\n{items}\n\n> Explicación: porque sí.\n"


class Quiz:
    """Un directorio quiz/ de prueba y una forma de correr el sync sobre él."""

    def __init__(self, root: Path, database_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
        self.root = root
        monkeypatch.setenv("DATABASE_URL", database_url)
        monkeypatch.setenv("QUIZ_DIR", str(root))

    def write(self, category: str, topic: str, *blocks: str) -> None:
        path = self.root / category / f"{topic}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(blocks), encoding="utf-8")

    def sync(self) -> int:
        return main()
