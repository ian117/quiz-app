"""Parser y validador de la convención de quiz/*.md.

Es la única implementación de la convención: la usan los hooks de
.claude/hooks y el script sync. Si cambia la convención, cambia aquí.

Estructura esperada: quiz/<categoria>/<tema>.md
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

CATEGORIES = {"frontend", "backend", "cloud", "ai", "fundamentos", "hr"}

# Tags que vienen de la regla de normalización de marcas del repo fuente.
MARKER_TAGS = {"frecuente", "senior", "real"}
# Tags que parecen marcas inventadas o dificultad (descartada por decisión).
FORBIDDEN_TAGS = {
    "importante", "esencial", "clave", "top", "comun", "frecuentes",
    "muy-frecuente", "basica", "basico", "intermedia", "intermedio",
    "avanzada", "avanzado", "dificil", "facil", "dificultad",
}

SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
OPTION = re.compile(r"^- \[( |x)\] (\S.*)$")
OPTION_LIKE = re.compile(r"^\s*[-*+]\s*\[.?\]")
TAGS_LINE = re.compile(r"^tags:\s*(.*)$")
EXPL_START = re.compile(r"^>\s?Explicación:\s*(.*)$")
FENCE = re.compile(r"^\s*(```|~~~)")

SHORT = 20       # si todas las opciones miden <= SHORT, no se compara el largo
MAX_RATIO = 2.5  # opción más larga / más corta
TELL = 1.3       # la correcta no puede superar en >30% a la distractora más larga


@dataclass
class Option:
    text: str
    correct: bool


@dataclass
class Question:
    key: str
    line: int
    position: int
    prompt_md: str = ""
    options: list[Option] = field(default_factory=list)
    explanation_md: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass
class Issue:
    file: str
    line: int
    key: str | None
    msg: str

    def __str__(self) -> str:
        where = f"[{self.key}] " if self.key else ""
        return f"{self.file}:{self.line} {where}{self.msg}"


def _visible_len(text: str) -> int:
    """Largo sin marcas de markdown (`, *, _) para comparar opciones."""
    return len(re.sub(r"[`*_]", "", text).strip())


def parse_text(text: str, file: str = "<texto>") -> tuple[list[Question], list[Issue]]:
    questions: list[Question] = []
    issues: list[Issue] = []
    cur: Question | None = None
    state = "prompt"          # prompt -> options -> explanation -> done
    prompt: list[str] = []
    expl: list[str] = []
    in_fence = False
    fence_line = 0

    def err(n: int, msg: str) -> None:
        issues.append(Issue(file, n, cur.key if cur else None, msg))

    def close() -> None:
        if cur is None:
            return
        cur.prompt_md = "\n".join(prompt).strip()
        cur.explanation_md = "\n".join(expl).strip()
        questions.append(cur)

    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip()

        # Dentro de un bloque de código todo es contenido, incluso '## ' o '- [ ]'.
        quoted = line[1:].lstrip() if line.startswith(">") else line
        if FENCE.match(quoted):
            in_fence = not in_fence
            fence_line = n
            if cur is not None and state == "prompt":
                prompt.append(line)
            elif cur is not None and state == "explanation" and line.startswith(">"):
                expl.append(re.sub(r"^>\s?", "", line))
            elif cur is not None:
                err(n, "bloque de código fuera de la pregunta o de la explicación")
            continue
        if in_fence:
            if cur is not None and state == "prompt":
                prompt.append(line)
            elif cur is not None and state == "explanation":
                expl.append(re.sub(r"^>\s?", "", line))
            continue

        if line.startswith("## "):
            close()
            cur = Question(key=line[3:].strip(), line=n, position=len(questions) + 1)
            state, prompt, expl = "prompt", [], []
            continue
        if cur is None:
            if line.strip() and not line.startswith("# "):
                issues.append(Issue(file, n, None, "texto antes del primer '## key' (solo se permite un título '# ...')"))
            continue

        m_opt = OPTION.match(line)
        m_expl = EXPL_START.match(line)

        if state == "prompt":
            m_tags = TAGS_LINE.match(line)
            if m_tags:
                if cur.tags:
                    err(n, "hay más de una línea 'tags:'")
                cur.tags = [t.strip() for t in m_tags.group(1).split(",") if t.strip()]
            elif m_opt:
                state = "options"
                cur.options.append(Option(m_opt.group(2).strip(), m_opt.group(1) == "x"))
            elif m_expl:
                err(n, "la explicación aparece antes de las opciones")
                state = "explanation"
                expl.append(m_expl.group(1))
            elif OPTION_LIKE.match(line):
                err(n, "opción mal formada: usa '- [ ] texto' o '- [x] texto'")
            else:
                prompt.append(line)
        elif state == "options":
            if m_opt:
                cur.options.append(Option(m_opt.group(2).strip(), m_opt.group(1) == "x"))
            elif m_expl:
                state = "explanation"
                expl.append(m_expl.group(1))
            elif OPTION_LIKE.match(line):
                err(n, "opción mal formada: usa '- [ ] texto' o '- [x] texto'")
            elif line.strip():
                err(n, "texto inesperado entre las opciones (cada opción va en una sola línea)")
        elif state == "explanation":
            if line.startswith(">"):
                expl.append(re.sub(r"^>\s?", "", line))
            elif line.strip():
                state = "done"
                err(n, "texto después de la explicación: todo el bloque '>' es la explicación")
        elif line.strip():
            err(n, "texto después de la explicación")

    if in_fence:
        issues.append(Issue(file, fence_line, cur.key if cur else None, "bloque de código sin cerrar"))
    close()
    return questions, issues


def check_question(q: Question, topic: str | None, file: str) -> list[Issue]:
    out: list[Issue] = []

    def err(msg: str) -> None:
        out.append(Issue(file, q.line, q.key, msg))

    if not SLUG.match(q.key):
        err("la key debe ser un slug: minúsculas, números y guiones")
    elif topic and not q.key.startswith(f"{topic}-"):
        err(f"la key debe empezar con el tema: '{topic}-...'")

    first = next((l for l in q.prompt_md.splitlines() if l.strip()), "")
    if not first:
        err("falta la pregunta")
    elif FENCE.match(first):
        err("la primera línea debe ser el texto de la pregunta, no un bloque de código")

    correct = [o for o in q.options if o.correct]
    wrong = [o for o in q.options if not o.correct]
    if len(correct) != 1:
        err(f"debe haber exactamente un [x] (hay {len(correct)})")
    if len(wrong) < 3:
        err(f"debe haber al menos tres [ ] (hay {len(wrong)})")
    texts = [o.text.lower() for o in q.options]
    if len(set(texts)) != len(texts):
        err("hay opciones repetidas")

    if len(correct) == 1 and wrong:
        lens = [_visible_len(o.text) for o in q.options]
        if max(lens) > SHORT:
            if max(lens) / max(min(lens), 1) > MAX_RATIO:
                err(f"las opciones difieren demasiado en largo (máx/mín > {MAX_RATIO})")
            c, w = _visible_len(correct[0].text), max(_visible_len(o.text) for o in wrong)
            if c > TELL * w:
                err(f"la correcta es notablemente la más larga ({c} vs {w} caracteres): "
                    "alarga los distractores o acorta la correcta")

    if not q.explanation_md:
        err("falta la explicación: '> Explicación: ...'")

    if len(set(q.tags)) != len(q.tags):
        err("hay tags repetidos")
    for t in q.tags:
        if not SLUG.match(t):
            err(f"tag '{t}' inválido: usa minúsculas, números y guiones, sin acentos")
        elif t in FORBIDDEN_TAGS:
            err(f"tag '{t}' no permitido: las marcas se normalizan solo a "
                f"{sorted(MARKER_TAGS)} y la dificultad no se etiqueta (skill quiz-format)")
    return out


def topic_from_path(path: Path, quiz_root: Path) -> tuple[str | None, str | None, list[str]]:
    """Devuelve (categoria, tema, errores de ubicación)."""
    try:
        rel = path.resolve().relative_to(quiz_root.resolve())
    except ValueError:
        return None, None, ["el archivo no está dentro de quiz/"]
    parts = rel.parts
    if len(parts) != 2 or path.suffix != ".md":
        return None, None, ["ubicación inválida: debe ser quiz/<categoria>/<tema>.md"]
    cat, topic = parts[0], path.stem
    errs = []
    if cat not in CATEGORIES:
        errs.append(f"categoría '{cat}' desconocida: usa una de {sorted(CATEGORIES)}")
    if not SLUG.match(topic):
        errs.append(f"nombre de tema '{topic}' inválido: debe ser un slug")
    return cat, topic, errs


def validate_file(path: Path, quiz_root: Path) -> tuple[list[Question], list[Issue]]:
    rel = str(path)
    _, topic, loc_errs = topic_from_path(path, quiz_root)
    issues = [Issue(rel, 1, None, e) for e in loc_errs]
    questions, parse_issues = parse_text(path.read_text(encoding="utf-8"), rel)
    issues += parse_issues
    if not questions:
        issues.append(Issue(rel, 1, None, "no hay ningún bloque '## key'"))
    seen: set[str] = set()
    for q in questions:
        issues += check_question(q, topic, rel)
        if q.key in seen:
            issues.append(Issue(rel, q.line, q.key, "key duplicada en este archivo"))
        seen.add(q.key)
    return questions, issues


def quiz_files(quiz_root: Path) -> list[Path]:
    return sorted(p for p in quiz_root.rglob("*.md") if p.is_file())


def validate_tree(quiz_root: Path) -> list[Issue]:
    issues: list[Issue] = []
    owners: dict[str, str] = {}
    for p in quiz_files(quiz_root):
        questions, file_issues = validate_file(p, quiz_root)
        issues += file_issues
        for q in questions:
            if q.key in owners and owners[q.key] != str(p):
                issues.append(Issue(str(p), q.line, q.key, f"key ya usada en {owners[q.key]}"))
            owners.setdefault(q.key, str(p))
    return issues


@dataclass
class TopicFile:
    category: str
    topic: str
    path: Path
    questions: list[Question]


def load_tree(quiz_root: Path) -> list[TopicFile]:
    """Para el sync: valida todo y, si no hay errores, devuelve el contenido."""
    issues = validate_tree(quiz_root)
    if issues:
        raise ValueError("quiz inválido:\n" + "\n".join(f"- {i}" for i in issues))
    out = []
    for p in quiz_files(quiz_root):
        cat, topic, _ = topic_from_path(p, quiz_root)
        questions, _ = validate_file(p, quiz_root)
        out.append(TopicFile(cat, topic, p, questions))  # type: ignore[arg-type]
    return out
