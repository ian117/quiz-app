# quiz-app

Juego de opción múltiple (uso personal, sin login) para practicar las preguntas de entrevista de `ment-it-questions`. La visión y las decisiones están en `docs/vision.md`: léela antes de tocar el modelo de datos, la API o los modos de juego.

## Mapa

- `../ment-it-questions/`: repo fuente (prosa), **solo lectura**. Lanza con `claude --add-dir ../ment-it-questions`.
- `quiz/<categoria>/<tema>.md`: fuente de verdad del quiz. La convención está en la skill `quiz-format`.
- `quizfmt/`: parser y validador del quiz, compartido por los hooks y el sync. Protegido.
- `backend/` (incluye el sync, que es un adaptador de entrada: `app/cli/sync.py`), `frontend/`, `docker-compose.yml`: cada uno tiene su regla en `.claude/rules/`, que se carga al tocarlo.
- `docker compose up` levanta db → sync → api → web (existen los cuatro; el web en http://localhost:5173). El contrato de la API es `backend/openapi.json`.

## Cómo trabajar

- Tú construyes backend (con el sync) y frontend **en secuencia**: comparten el contrato (modelo y OpenAPI). No los delegues a subagentes.
- Los subagentes son solo para tareas independientes o verificación imparcial: `question-converter`, `quiz-reviewer`, `ux-reviewer`.
- Convierte preguntas solo cuando la persona ejecute `/convert-batch`.
- Hay decisiones abiertas (por ejemplo, la librería de componentes): pregunta antes de decidirlas. Están listadas en `docs/vision.md`.
- Por qué el harness es así: `docs/harness.md`.

## Hooks (no intentes evitarlos)

- Bloquean escrituras en el repo fuente, `.claude/hooks/`, `.claude/settings.json` y `quizfmt/`.
- Validan cada `quiz/*.md` al escribirlo y pasan el linter al código editado.
- Al terminar cada turno revisan todo: quiz, repo fuente intacto, arquitectura, tipos y tests.
