# quiz-app

Juego de opción múltiple (uso personal, sin login) para practicar las preguntas de entrevista de `ment-it-questions`. La visión y las decisiones están en `docs/vision.md`: léela antes de tocar el modelo de datos, la API o los modos de juego.

## Mapa

- `../ment-it-questions/`: repo privado con **todo el contenido**: prosa y `quiz/<categoria>/<tema>.md`, la fuente de verdad del quiz. Aquí es **solo lectura**. Lanza con `claude --add-dir ../ment-it-questions`.
- La convención del quiz: la implementa `quizfmt/` (abajo) y la explica la skill `quiz-format`, en `../ment-it-questions/.claude/skills/`.
- `quizfmt/`: parser y validador del quiz, compartido por los hooks y el sync. Protegido.
- `backend/` (incluye el sync, que es un adaptador de entrada: `app/cli/sync.py`), `frontend/`, `docker-compose.yml`: cada uno tiene su regla en `.claude/rules/`, que se carga al tocarlo.
- `docker compose up` levanta db → sync → api → web (existen los cuatro; el web en http://localhost:5173). El contrato de la API es `backend/openapi.json`.

## Cómo trabajar

- Tú construyes backend (con el sync) y frontend **en secuencia**: comparten el contrato (modelo y OpenAPI). No los delegues a subagentes.
- El único subagente aquí es `ux-reviewer` (verificación imparcial de la UI).
- **Aquí no se escriben ni se convierten preguntas:** eso se hace en `ment-it-questions` (`/registrar-entrevista`, `tools/convert.py`).
- Hay decisiones abiertas (por ejemplo, la librería de componentes): pregunta antes de decidirlas. Están listadas en `docs/vision.md`.
- Por qué el harness es así: `docs/harness.md`.

## Hooks (no intentes evitarlos)

- Bloquean escrituras en el repo fuente, `.claude/hooks/`, `.claude/settings.json` y `quizfmt/`.
- Pasan el linter al código editado.
- Al terminar cada turno revisan: repo fuente sin cambios hechos en esta sesión, arquitectura, tipos y tests. Si el quiz tiene errores solo avisan: se corrigen en `ment-it-questions`.
