"""Utilidades compartidas por los hooks."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2]).resolve()
# Repo fuente: carpeta hermana por defecto; se puede cambiar con QUIZ_SOURCE_DIR.
SOURCE = Path(os.environ.get("QUIZ_SOURCE_DIR") or ROOT.parent / "ment-it-questions").resolve()
# El quiz vive en el repo fuente (privado); este repo es público.
QUIZ = (SOURCE / "quiz").resolve()

PROTECTED = [
    SOURCE,
    ROOT / ".claude" / "hooks",
    ROOT / ".claude" / "settings.json",
    ROOT / "quizfmt",
]

sys.path.insert(0, str(ROOT))


def read_input() -> dict:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}


def target_path(data: dict) -> Path | None:
    ti = data.get("tool_input") or {}
    fp = ti.get("file_path") or ti.get("notebook_path")
    if not fp:
        return None
    p = Path(fp)
    if not p.is_absolute():
        p = Path(data.get("cwd") or ROOT) / p
    return p.resolve()


def is_under(p: Path, base: Path) -> bool:
    return p == base or base in p.parents


def rel(p: Path) -> str:
    return str(p.relative_to(ROOT)) if is_under(p, ROOT) else str(p)


def run(cmd: list[str], cwd: Path, timeout: int = 180) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout + r.stderr).strip()
    except subprocess.TimeoutExpired:
        return 1, f"{' '.join(cmd)}: tardó más de {timeout}s"


def tool(name: str, *local_dirs: Path) -> str | None:
    """Busca una herramienta en node_modules/.bin o .venv/bin locales, y luego en el PATH."""
    for d in local_dirs:
        for sub in ("node_modules/.bin", ".venv/bin"):
            c = d / sub / name
            if c.exists():
                return str(c)
    return shutil.which(name)


def fail(title: str, lines: list[str]) -> None:
    print(title, file=sys.stderr)
    print("\n".join(f"- {line}" for line in lines), file=sys.stderr)
    sys.exit(2)
