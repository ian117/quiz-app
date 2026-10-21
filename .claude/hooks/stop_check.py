#!/usr/bin/env python3
"""Stop: revisión completa al terminar cada turno.

Cubre lo que los hooks por herramienta no ven (escrituras hechas con Bash):
1. El quiz (en el repo fuente) cumple la convención. Solo avisa: se corrige allá.
2. El repo fuente no tiene cambios hechos durante esta sesión (los tuyos de antes no cuentan).
3. Arquitectura hexagonal (import-linter), si el backend ya lo tiene configurado.
4. Tipos del frontend (tsc --noEmit), si ya hay node_modules.
5. Tests de backend/sync, solo si esas carpetas tienen cambios sin commitear.

exit 2 = Claude no termina y recibe la lista para corregir.
Si este hook ya bloqueó una vez seguida (stop_hook_active), no vuelve a bloquear,
para evitar un bucle; los problemas quedan a la vista de la persona.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

from _common import QUIZ, ROOT, SOURCE, read_input, run, tool

data = read_input()
problems: list[str] = []
warnings: list[str] = []

# 1. Quiz: el contenido es del repo fuente, así que aquí solo se avisa.
if QUIZ.is_dir():
    from quizfmt import validate_tree

    issues = validate_tree(QUIZ)
    if issues:
        warnings.append(
            f"el quiz ({QUIZ}) tiene {len(issues)} error(es); el sync fallará. "
            "Se corrigen en ment-it-questions, no aquí:\n" + "\n".join(f"  {i}" for i in issues[:10])
        )


def session_start() -> float | None:
    """Hora de inicio de la sesión, según el primer mensaje del transcript."""
    tp = data.get("transcript_path")
    if not tp or not Path(tp).exists():
        return None
    with open(tp, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                ts = json.loads(line).get("timestamp")
            except (json.JSONDecodeError, AttributeError):
                continue
            if ts:
                try:
                    return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
                except ValueError:
                    return None
    return None


# 2. Repo fuente sin cambios de esta sesión (atrapa escrituras hechas con Bash).
# Los cambios que la persona ya tenía (por ejemplo, preguntas nuevas sin commitear) no cuentan.
if (SOURCE / ".git").exists():
    code, out = run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=SOURCE, timeout=30)
    if code == 0 and out:
        start = session_start()
        # "XY ruta" o "R  vieja -> nueva"; run() recorta el espacio inicial de la primera línea.
        paths = [line.split(maxsplit=1)[1].split(" -> ")[-1].strip('"') for line in out.splitlines() if line.strip()]
        if start is None:
            touched = paths
        else:
            touched = [
                rel for rel in paths
                if (SOURCE / rel).exists() and (SOURCE / rel).stat().st_mtime > start
            ]
        if touched:
            problems.append(
                f"el repo fuente ({SOURCE}) es de solo lectura y cambió durante esta sesión: "
                + ", ".join(touched[:10])
                + f". Revísalo con `git -C {SOURCE} status` y revierte solo lo que hiciste tú."
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

if warnings:
    print("Aviso:\n" + "\n".join(f"- {w}" for w in warnings), file=sys.stderr)

if problems:
    if data.get("stop_hook_active"):
        print("Siguen pendientes (no se bloquea de nuevo):\n" + "\n".join(problems), file=sys.stderr)
        sys.exit(1)
    print("Antes de terminar, corrige esto:", file=sys.stderr)
    print("\n".join(f"- {p}" for p in problems), file=sys.stderr)
    sys.exit(2)

if warnings:
    sys.exit(1)  # se muestra a la persona sin bloquear
