#!/usr/bin/env python3
"""PostToolUse (Write|Edit|MultiEdit): revisa el archivo recién escrito.

- quiz/**/*.md        -> convención del quiz (quizfmt), incluidas keys duplicadas entre archivos
- backend|sync/**/*.py -> ruff check (si está instalado)
- frontend/**/*.ts(x)  -> eslint (si está instalado en frontend/node_modules)

exit 2 = el agente ve los errores y debe corregirlos. Si una herramienta aún no
existe (scaffolding a medio hacer), se omite sin bloquear.
"""
from _common import QUIZ, ROOT, fail, is_under, read_input, rel, run, target_path, tool

p = target_path(read_input())
if not p or not p.exists():
    raise SystemExit(0)

if is_under(p, QUIZ) and p.suffix == ".md":
    from quizfmt import quiz_files, validate_file

    questions, mine = validate_file(p, QUIZ)
    others = {}
    for other in quiz_files(QUIZ):
        if other.resolve() != p:
            for q in validate_file(other, QUIZ)[0]:
                others[q.key] = rel(other)
    mine += [f"{rel(p)}:{q.line} [{q.key}] key ya usada en {others[q.key]}" for q in questions if q.key in others]
    if mine:
        fail(f"Errores de formato en {rel(p)}. Corrígelos (convención: skill quiz-format):", [str(i) for i in mine])

elif p.suffix == ".py" and (is_under(p, ROOT / "backend") or is_under(p, ROOT / "sync")):
    base = ROOT / ("backend" if is_under(p, ROOT / "backend") else "sync")
    ruff = tool("ruff", base, ROOT)
    if ruff:
        code, out = run([ruff, "check", str(p)], cwd=base, timeout=60)
        if code:
            fail(f"ruff encontró problemas en {rel(p)}:", out.splitlines()[:40])

elif p.suffix in (".ts", ".tsx") and is_under(p, ROOT / "frontend"):
    eslint = ROOT / "frontend" / "node_modules" / ".bin" / "eslint"
    if eslint.exists():
        code, out = run([str(eslint), str(p)], cwd=ROOT / "frontend", timeout=60)
        if code:
            fail(f"eslint encontró problemas en {rel(p)}:", out.splitlines()[:40])
