#!/usr/bin/env python3
"""Convierte un tema por lotes, cada lote en una sesión nueva de Claude Code.

Por qué existe (ver docs/harness.md, "Costo de la conversión"): si un solo agente
principal orquesta muchos lotes, su contexto crece con cada resultado y cada
llamada relee todo lo anterior. Aquí la orquestación es un bucle de Python, que
no gasta tokens, y cada lote empieza con el contexto vacío.

Uso (desde la raíz del repo, en el host):
    python3 tools/convert.py ../ment-it-questions/.../preguntas-entrevista-react.md frontend/react --lotes 1-10 11-20
    python3 tools/convert.py <fuente.md> frontend/react --todo            # todos, de 10 en 10
    python3 tools/convert.py <fuente.md> frontend/react --todo --solo-extraer

Por cada lote:
1. Extrae leyenda + preguntas a `.convert/<tema>-<a>-<b>.md` (tools/extract_batch.py).
2. Ejecuta `claude -p "/convert-batch <extracto> quiz/<categoria>/<tema>.md"`.
3. Guarda el resultado y el costo estimado en `.convert/<tema>-<a>-<b>.json`.
Un lote con su .json en estado ok se salta (puedes relanzar el comando tras un corte).
Se detiene en el primer lote que falle.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_batch import parse_range, parse_source, render_batch

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / ".convert"
CATEGORIES = {"frontend", "backend", "cloud", "ai", "fundamentos", "hr"}


def batches(all_numbers: list[int], size: int) -> list[tuple[int, int]]:
    nums = sorted(set(all_numbers))
    return [(chunk[0], chunk[-1]) for chunk in (nums[i:i + size] for i in range(0, len(nums), size))]


def run_claude(extract: Path, dest: Path, model: str, budget: float | None) -> dict:
    cmd = [
        "claude", "-p", f"/convert-batch {extract.relative_to(ROOT)} {dest.relative_to(ROOT)}",
        "--model", model,
        "--permission-mode", "acceptEdits",
        "--allowedTools", "Read,Grep,Glob,Edit,Write,Agent",
        "--output-format", "json",
    ]
    if budget:
        cmd += ["--max-budget-usd", str(budget)]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError:
        data = {"result": r.stdout.strip(), "is_error": True}
    data["exit_code"] = r.returncode
    if r.stderr.strip():
        data["stderr"] = r.stderr.strip()[-2000:]
    return data


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", type=Path, help="archivo del repo fuente")
    ap.add_argument("target", help="<categoria>/<tema>, por ejemplo frontend/react")
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--lotes", nargs="+", help="rangos con los números del fuente: 1-10 11-20")
    group.add_argument("--todo", action="store_true", help="todas las preguntas, en lotes de --tam")
    ap.add_argument("--tam", type=int, default=10, help="tamaño de lote con --todo (10)")
    ap.add_argument("--modelo", default="sonnet", help="modelo del agente principal de cada lote (sonnet)")
    ap.add_argument("--max-usd", type=float, help="tope de costo estimado por lote (--max-budget-usd)")
    ap.add_argument("--solo-extraer", action="store_true", help="solo genera los extractos, sin llamar a Claude")
    args = ap.parse_args(argv)

    category, _, topic = args.target.partition("/")
    if category not in CATEGORIES or not topic or "/" in topic:
        ap.error(f"target debe ser <categoria>/<tema> con categoria en {sorted(CATEGORIES)}")
    if not args.source.is_file():
        ap.error(f"no existe {args.source}")
    if not args.solo_extraer and not shutil.which("claude"):
        ap.error("no encuentro el comando `claude` en el PATH")

    src = parse_source(args.source.read_text(encoding="utf-8"))
    ranges = [parse_range(s) for s in args.lotes] if args.lotes else batches([q.number for q in src.questions], args.tam)
    dest = ROOT / "quiz" / category / f"{topic}.md"

    total_usd, done = 0.0, 0
    for a, b in ranges:
        name = f"{topic}-{a}-{b}"
        extract, report = WORK / f"{name}.md", WORK / f"{name}.json"
        text, numbers = render_batch(src, str(args.source), a, b)
        if not numbers:
            print(f"[{name}] sin preguntas en ese rango; se omite")
            continue
        WORK.mkdir(exist_ok=True)
        extract.write_text(text, encoding="utf-8")
        print(f"[{name}] extracto: {len(numbers)} pregunta(s), {len(text):,} caracteres")
        if args.solo_extraer:
            continue
        if report.exists() and json.loads(report.read_text(encoding="utf-8")).get("ok"):
            print(f"[{name}] ya convertido ({report.name}); se omite")
            continue

        data = run_claude(extract, dest, args.modelo, args.max_usd)
        data["ok"] = data["exit_code"] == 0 and not data.get("is_error")
        report.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        usd = data.get("total_cost_usd") or 0.0
        total_usd += usd
        print(f"[{name}] {'OK' if data['ok'] else 'FALLÓ'} · costo estimado ${usd:.2f}\n")
        print(data.get("result", "").strip(), "\n")
        if not data["ok"]:
            print(f"Detalle en {report.relative_to(ROOT)}. Corrige y relanza el mismo comando.")
            return 1
        done += 1

    if not args.solo_extraer:
        print(f"Lotes convertidos: {done} · costo estimado total ${total_usd:.2f}")
        print(f"Revisa {dest.relative_to(ROOT)} y estudia el lote antes de seguir. Validación a mano: python3 -m quizfmt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
