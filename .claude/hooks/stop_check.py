#!/usr/bin/env python3
"""Stop: revisión completa al terminar cada turno.

Cubre lo que los hooks por herramienta no ven (escrituras hechas con Bash):
1. Todo quiz/ cumple la convención.
2. El repo fuente no tiene cambios.
3. Arquitectura hexagonal (import-linter), si el backend ya lo tiene configurado.
4. Tipos del frontend (tsc --noEmit), si ya hay node_modules.
5. Tests de backend/sync, solo si esas carpetas tienen cambios sin commitear.

exit 2 = Claude no termina y recibe la lista para corregir.
Si este hook ya bloqueó una vez seguida (stop_hook_active), no vuelve a bloquear,
para evitar un bucle; los problemas quedan a la vista de la persona.
"""
import sys

from _common import QUIZ, ROOT, SOURCE, read_input, run, tool

data = read_input()
problems: list[str] = []

# 1. Quiz
if QUIZ.is_dir():
    from quizfmt import validate_tree

    problems += [f"quiz: {i}" for i in validate_tree(QUIZ)]

# 2. Repo fuente intacto
if (SOURCE / ".git").exists():
    code, out = run(["git", "status", "--porcelain"], cwd=SOURCE, timeout=30)
    if code == 0 and out:
        problems.append(
            f"el repo fuente ({SOURCE}) tiene cambios y es de solo lectura. "
            f"Revísalos con `git -C {SOURCE} status` y revierte los que hiciste."
        )


def changed(folder: str) -> bool:
    code, out = run(["git", "status", "--porcelain", "--", folder], cwd=ROOT, timeout=30)
    return code == 0 and bool(out)


backend = ROOT / "backend"
# 3. Arquitectura
pyproject = backend / "pyproject.toml"
has_contracts = (backend / ".importlinter").exists() or (
    pyproject.exists() and "[tool.importlinter]" in pyproject.read_text(encoding="utf-8")
)
lint_imports = tool("lint-imports", backend, ROOT)
if has_contracts and lint_imports:
    code, out = run([lint_imports], cwd=backend)
    if code:
        problems.append("import-linter (arquitectura hexagonal):\n" + "\n".join(out.splitlines()[-30:]))

# 4. Tipos del frontend
tsc = ROOT / "frontend" / "node_modules" / ".bin" / "tsc"
if tsc.exists() and (ROOT / "frontend" / "tsconfig.json").exists():
    code, out = run([str(tsc), "--noEmit", "-p", "."], cwd=ROOT / "frontend")
    if code:
        problems.append("tsc --noEmit:\n" + "\n".join(out.splitlines()[:30]))

# 5. Tests (solo si hubo cambios)
for folder in ("backend", "sync"):
    base = ROOT / folder
    pytest = tool("pytest", base, ROOT)
    if (base / "tests").is_dir() and pytest and changed(folder):
        code, out = run([pytest, "-q", "-x"], cwd=base, timeout=300)
        if code not in (0, 5):  # 5 = no se recolectaron tests
            problems.append(f"pytest en {folder}/:\n" + "\n".join(out.splitlines()[-30:]))

if problems:
    if data.get("stop_hook_active"):
        print("Siguen pendientes (no se bloquea de nuevo):\n" + "\n".join(problems), file=sys.stderr)
        sys.exit(1)
    print("Antes de terminar, corrige esto:", file=sys.stderr)
    print("\n".join(f"- {p}" for p in problems), file=sys.stderr)
    sys.exit(2)
