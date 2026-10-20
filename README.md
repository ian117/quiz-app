# quiz-app

Juego de opción múltiple para practicar las preguntas de entrevista de `ment-it-questions`.

- Visión y decisiones: [`docs/vision.md`](docs/vision.md)
- Cómo trabajan los agentes: [`docs/harness.md`](docs/harness.md)

## Puesta en marcha (host)

Requisitos: Python ≥ 3.10 (para `quizfmt` y los hooks), [uv](https://docs.astral.sh/uv/), Docker, Claude Code y git con SSH hacia GitHub.

```bash
# 1. Repo fuente, junto a este (con tu SSH)
git clone git@github.com:ian117/ment-it-questions.git ../ment-it-questions

# 2. Preferencias personales (una vez; si ya tienes ~/.claude/CLAUDE.md, añade el contenido al final)
mkdir -p ~/.claude && cat user-claude/CLAUDE.md >> ~/.claude/CLAUDE.md

# 3. Claude Code con acceso de lectura al repo fuente
claude --add-dir ../ment-it-questions
```

### Entorno del backend (Python 3.12)

El backend exige `requires-python >= 3.12`, como la imagen de Docker. El host puede traer otra versión, así que el venv lo crea uv, y los hooks usan `backend/.venv`:

```bash
# Instalar uv (una vez): https://docs.astral.sh/uv/getting-started/installation/
curl -LsSf https://astral.sh/uv/install.sh | sh

cd backend
uv venv --python 3.12   # descarga Python 3.12 si hace falta
uv sync                 # instala según uv.lock (incluye ruff, pytest, import-linter)
```

`uv.lock` se commitea. Si cambias las dependencias en `pyproject.toml`, ejecuta `uv lock` y commitea también el lock: la imagen instala con `uv sync --frozen`.

Si `ment-it-questions` está en otra ruta, exporta `QUIZ_SOURCE_DIR=/ruta/absoluta` antes de lanzar `claude`, para que los hooks lo protejan.

## Uso

| Qué | Comando |
|---|---|
| Convertir un lote de preguntas | `/convert-batch react 1-10` (dentro de Claude Code) |
| Validar el quiz a mano | `python3 -m quizfmt` |
| Tests del parser | `python3 quizfmt/test_quizfmt.py` |
| Levantar todo (`db`, `sync`, `api` y `web`) | `docker compose up` (juego en http://localhost:5173, API en http://localhost:8000, docs en `/docs`) |
| Frontend en desarrollo | `cd frontend && npm ci && npm run dev` (con la API ya levantada) |
| Checks del frontend | `cd frontend && npm run lint && npm run typecheck && npm test` |
| Regenerar los tipos de la API | `cd frontend && npm run gen:api` (tras regenerar `backend/openapi.json`) |
| Re-sincronizar el quiz | `docker compose run --rm sync` |
| Tests del backend (unitarios + integración) | `docker compose up -d db`, luego `cd backend && .venv/bin/pytest -q` |
| Regenerar el contrato de la API | `cd backend && PYTHONPATH=.:.. .venv/bin/python -m app.api.openapi > openapi.json` |
| Arquitectura hexagonal | `cd backend && .venv/bin/lint-imports` |
| Nueva migración | `cd backend && DATABASE_URL=postgresql+psycopg://quiz:quiz@localhost:5432/quiz .venv/bin/alembic revision --autogenerate -m "..."` |

Los tests de integración usan la base `quiz_test`, nunca `quiz` (guarda el historial). No uses `docker compose down -v` sin respaldo: borra el volumen con el historial.

## Estado

Listo: el harness (reglas, skills, subagentes, hooks), el parser/validador, el modelo de datos con sus migraciones, el sync, la API y el frontend (`db`, `sync`, `api` y `web` en compose) y las preguntas de React convertidas hasta ahora.

Pendiente: seguir convirtiendo lotes de React con `/convert-batch`.
