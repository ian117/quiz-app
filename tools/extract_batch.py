#!/usr/bin/env python3
"""Extrae un lote de preguntas del repo fuente a un archivo pequeño.

Así los agentes leen solo la leyenda y las preguntas del lote, no el archivo
fuente completo (50-77 preguntas en prosa) en cada invocación.

Uso:
    python3 tools/extract_batch.py <fuente.md> --list
    python3 tools/extract_batch.py <fuente.md> 1-10 -o .convert/react-1-10.md

Formatos que reconoce (ver docs/vision.md, "Repo fuente"):
- 100-interview-questions: `### N. ¿Pregunta? ⭐` o `#### N. ...`, agrupadas en `## Sección N: <subtema>`.
- real-interviews: `### Pregunta` sin número; se numeran por orden (1, 2, 3...).
La leyenda es el párrafo que empieza con `**Leyenda`. Se copia tal cual.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

FENCE = re.compile(r"^\s*(```|~~~)")
SECTION = re.compile(r"^##\s+\S")
NUMBERED = re.compile(r"^#{3,4}\s+(\d+)[.)]\s*\S")
LEVEL3 = re.compile(r"^###\s+\S")
LEGEND = re.compile(r"^\s*\*\*Leyenda", re.IGNORECASE)
RULE = re.compile(r"^\s*(-{3,}|\*{3,})\s*$")


@dataclass
class SourceQuestion:
    number: int
    title: str
    section: str | None
    lines: list[str] = field(default_factory=list)


@dataclass
class SourceFile:
    legend: str | None
    questions: list[SourceQuestion]


def _strip_tail(lines: list[str]) -> list[str]:
    while lines and (not lines[-1].strip() or RULE.match(lines[-1])):
        lines.pop()
    return lines


def parse_source(text: str) -> SourceFile:
    lines = text.splitlines()

    # Pasada 1: ¿el archivo numera sus preguntas? (fuera de bloques de código)
    in_code, numbered = False, False
    for line in lines:
        if FENCE.match(line):
            in_code = not in_code
        elif not in_code and NUMBERED.match(line):
            numbered = True
            break

    legend: list[str] = []
    in_legend = False
    questions: list[SourceQuestion] = []
    section: str | None = None
    cur: SourceQuestion | None = None
    in_code = False

    def close() -> None:
        nonlocal cur
        if cur:
            _strip_tail(cur.lines)
            questions.append(cur)
        cur = None

    for line in lines:
        is_fence = bool(FENCE.match(line))
        heading = None if in_code else line
        if heading is not None and not is_fence:
            m = NUMBERED.match(line) if numbered else None
            if m or (not numbered and LEVEL3.match(line)):
                close()
                number = int(m.group(1)) if m else len(questions) + 1
                cur = SourceQuestion(number, line.lstrip("#").strip(), section, [line])
                in_legend = False
                continue
            if SECTION.match(line):
                close()
                section = line.strip()
                in_legend = False
                continue
            if LEGEND.match(line) and cur is None:
                in_legend = True
        if is_fence:
            in_code = not in_code
        if in_legend:
            if not line.strip():
                in_legend = False
            else:
                legend.append(line.rstrip())
        if cur is not None:
            cur.lines.append(line)
    close()
    return SourceFile("\n".join(legend) or None, questions)


def parse_range(spec: str) -> tuple[int, int]:
    m = re.fullmatch(r"(\d+)(?:-(\d+))?", spec.strip())
    if not m:
        raise ValueError(f"rango inválido: {spec!r} (usa 1-10 o 7)")
    a, b = int(m.group(1)), int(m.group(2) or m.group(1))
    if a > b:
        raise ValueError(f"rango invertido: {spec!r}")
    return a, b


def render_batch(src: SourceFile, source_path: str, a: int, b: int) -> tuple[str, list[int]]:
    picked = [q for q in src.questions if a <= q.number <= b]
    out = [
        f"# Lote: preguntas {a}-{b}",
        "",
        f"fuente: {source_path}",
        "",
        "## Leyenda del fuente (tal cual)",
        "",
        src.legend or "(el archivo no tiene leyenda: no pongas tags de frecuencia)",
        "",
        "## Preguntas",
    ]
    section = None
    for q in picked:
        if q.section != section:
            section = q.section
            out += ["", f"Sección del fuente: {section or '(sin sección)'}"]
        out += [""] + q.lines
    return "\n".join(out).rstrip() + "\n", [q.number for q in picked]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", type=Path)
    ap.add_argument("range", nargs="?", help="por ejemplo 1-10")
    ap.add_argument("-o", "--output", type=Path)
    ap.add_argument("--list", action="store_true", help="lista las preguntas que reconoce y termina")
    args = ap.parse_args(argv)

    src = parse_source(args.source.read_text(encoding="utf-8"))
    if args.list:
        print(f"leyenda: {'sí' if src.legend else 'no'} | preguntas: {len(src.questions)}")
        for q in src.questions:
            print(f"{q.number:>4}  {q.title[:90]}")
        return 0
    if not args.range:
        ap.error("falta el rango (o usa --list)")

    a, b = parse_range(args.range)
    text, numbers = render_batch(src, str(args.source), a, b)
    if not numbers:
        print(f"No hay preguntas {a}-{b} en {args.source} (tiene {len(src.questions)}).", file=sys.stderr)
        return 1
    missing = sorted(set(range(a, b + 1)) - set(numbers))
    if missing:
        print(f"Aviso: no encontré las preguntas {missing}.", file=sys.stderr)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(f"{args.output}: {len(numbers)} pregunta(s), {len(text):,} caracteres")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
