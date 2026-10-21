"""Tests de tools/ (extractor y orquestador). Ejecuta: python3 -m pytest tools -q"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import convert
from extract_batch import parse_range, parse_source, render_batch

NUMBERED = """# Preguntas de React

**Leyenda:** ⭐ = sale en casi todas las entrevistas
🎯 = distingue a un senior

## Sección 1: Fundamentos

### 1. ¿Qué es JSX? ⭐
Es azúcar sintáctico.

```js
// ### 99. esto es código, no una pregunta
const a = <div />;
```

---

### 2. ¿Qué es el Virtual DOM?
Una copia en memoria.

## Sección 2: Hooks

#### 3. ¿Qué hace useEffect? 🎯
Sincroniza con sistemas externos.
"""

REAL = """# Entrevistas reales: node

### ¿Qué es el event loop?
- Empresa / fecha: Acme, 2025
- Respuesta: coordina callbacks.

### ¿Qué es un stream?
- Empresa / fecha: Foo, 2026
- Respuesta: por completar
"""


def test_parse_numbered_ignores_code_and_tracks_sections():
    src = parse_source(NUMBERED)
    assert [q.number for q in src.questions] == [1, 2, 3]
    assert src.questions[0].section == "## Sección 1: Fundamentos"
    assert src.questions[2].section == "## Sección 2: Hooks"
    assert "### 99." in "\n".join(src.questions[0].lines)  # el código se queda dentro de la pregunta
    assert src.questions[0].lines[-1] == "```"  # se recorta el separador ---
    assert src.legend.startswith("**Leyenda:**") and "🎯" in src.legend


def test_parse_real_interviews_numbers_by_order():
    src = parse_source(REAL)
    assert [q.number for q in src.questions] == [1, 2]
    assert src.legend is None
    assert src.questions[1].title == "¿Qué es un stream?"


def test_render_batch_only_picks_range_with_sections_and_legend():
    src = parse_source(NUMBERED)
    text, numbers = render_batch(src, "fuente.md", 2, 3)
    assert numbers == [2, 3]
    assert "¿Qué es JSX?" not in text
    assert "**Leyenda:**" in text
    assert "Sección del fuente: ## Sección 1: Fundamentos" in text
    assert "Sección del fuente: ## Sección 2: Hooks" in text


def test_render_batch_without_legend_says_so():
    text, _ = render_batch(parse_source(REAL), "real-interviews/backend/node.md", 1, 2)
    assert "no tiene leyenda" in text and "real-interviews/" in text


def test_parse_range():
    assert parse_range("1-10") == (1, 10)
    assert parse_range("7") == (7, 7)
    for bad in ("10-1", "a-b", ""):
        try:
            parse_range(bad)
        except ValueError:
            continue
        raise AssertionError(bad)


def test_batches_groups_existing_numbers():
    assert convert.batches([1, 2, 3, 4, 5], 2) == [(1, 2), (3, 4), (5, 5)]
    assert convert.batches([1, 2, 4, 5], 3) == [(1, 4), (5, 5)]


def test_convert_runs_one_session_per_batch_and_resumes(tmp_path, monkeypatch):
    source = tmp_path / "react.md"
    source.write_text(NUMBERED, encoding="utf-8")
    monkeypatch.setattr(convert, "ROOT", tmp_path)
    monkeypatch.setattr(convert, "WORK", tmp_path / ".convert")
    monkeypatch.setattr(convert.shutil, "which", lambda _: "/usr/bin/claude")
    calls = []

    def fake_run(cmd, cwd, capture_output, text, check):
        calls.append(cmd)

        class R:
            returncode = 0
            stdout = json.dumps({"result": "| key | PASS |", "total_cost_usd": 0.5, "is_error": False})
            stderr = ""
        return R()

    monkeypatch.setattr(convert.subprocess, "run", fake_run)
    args = [str(source), "frontend/react", "--todo", "--tam", "2"]
    assert convert.main(args) == 0
    assert len(calls) == 2  # lotes 1-2 y 3-3, cada uno en su propio `claude -p`
    assert calls[0][2] == "/convert-batch .convert/react-1-2.md quiz/frontend/react.md"
    assert (tmp_path / ".convert" / "react-3-3.json").exists()

    calls.clear()
    assert convert.main(args) == 0
    assert calls == []  # los lotes ya convertidos se saltan


def test_convert_stops_on_first_failure(tmp_path, monkeypatch):
    source = tmp_path / "react.md"
    source.write_text(NUMBERED, encoding="utf-8")
    monkeypatch.setattr(convert, "ROOT", tmp_path)
    monkeypatch.setattr(convert, "WORK", tmp_path / ".convert")
    monkeypatch.setattr(convert.shutil, "which", lambda _: "/usr/bin/claude")
    calls = []

    def fake_run(cmd, cwd, capture_output, text, check):
        calls.append(cmd)

        class R:
            returncode = 1
            stdout = "error"
            stderr = "boom"
        return R()

    monkeypatch.setattr(convert.subprocess, "run", fake_run)
    assert convert.main([str(source), "frontend/react", "--todo", "--tam", "2"]) == 1
    assert len(calls) == 1
