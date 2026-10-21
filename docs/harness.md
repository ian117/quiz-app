# Harness: cómo trabajan los agentes en este repo

## Principio

Analogía: un edificio de oficinas.

| Pieza | En el edificio | Cuándo entra en contexto | Qué contiene aquí |
|---|---|---|---|
| `CLAUDE.md` | Directorio del vestíbulo | Siempre | Mapa corto (~25 líneas) |
| `.claude/rules/*.md` con `paths:` | Letrero en la puerta de cada piso | Al leer o editar archivos de esa carpeta | Reglas de backend, sync, frontend y docker |
| Skills | Manual en el archivero | Descripción siempre; cuerpo solo al usarla | Ninguna aquí; las del contenido viven en `ment-it-questions` |
| Hooks | Torniquetes | Siempre, y no dependen del modelo | Protección, validación, linters, tests |

**Regla para decidir:** ¿se necesita en todas las sesiones? Va en `CLAUDE.md`. ¿Solo al tocar ciertos archivos? Va en una regla con `paths`. ¿Es un procedimiento que se ejecuta a veces? Es una skill. ¿Tiene que cumplirse siempre? Es un hook. `CLAUDE.md` es contexto, no una restricción.

## Agentes

```
 ment-it-questions (contenido)              quiz-app (código, este repo)
 ┌───────────────────────────────┐          ┌──────────────────────────────┐
 │ /registrar-entrevista         │  quiz/   │ AGENTE PRINCIPAL             │
 │ tools/convert.py (backfill)   │ ──:ro──▶ │ sync → backend → frontend,   │
 │ question-converter,           │          │ en secuencia (un contrato)   │
 │ quiz-reviewer, quiz-format    │          └──────────────┬───────────────┘
 └───────────────────────────────┘                         │ tras cambios visibles
                                                           ▼
                                                      ux-reviewer
                                                      solo lectura + Bash
```

| Subagente | Por qué es un subagente |
|---|---|
| `ux-reviewer` | Verificación imparcial: quien escribió la UI no califica su propia UX |

**El contenido no se escribe aquí.** Este repo es público y el quiz es privado, así que las preguntas, su conversión y sus revisores viven en `ment-it-questions`. Aquí el quiz se lee en solo lectura: los hooks protegen todo ese repo, y el `Stop` solo avisa si el quiz tiene errores. El costo medido de la conversión y su rediseño están en `ment-it-questions/docs/conversion.md`.

- Los subagentes llevan `omitClaudeMd: true`: reciben su contexto por su propio prompt, y no se contaminan con el del principal.
- **Backend, sync y frontend no se delegan.** Los une un contrato (formato del md → modelo → API → tipos del front). Con un agente por capa, cada traspaso perdería contexto y multiplicaría el costo.

## Hooks

| Evento | Script | Qué hace |
|---|---|---|
| `PreToolUse` (Write, Edit, MultiEdit, NotebookEdit) | `protect_paths.py` | Bloquea escrituras en el repo fuente, `.claude/hooks/`, `.claude/settings.json` y `quizfmt/` |
| `PostToolUse` (Write, Edit, MultiEdit) | `post_edit.py` | `.py` de backend/sync → `ruff`; `.ts(x)` del frontend → `eslint` |
| `Stop` | `stop_check.py` | Repo fuente sin cambios **de esta sesión**, `import-linter`, `tsc --noEmit`, y `pytest` si hay cambios en backend/sync. El quiz inválido solo se avisa |

- Si una herramienta todavía no existe (scaffolding a medio hacer), el hook la omite sin bloquear.
- **El hueco de Bash:** un `sed -i` desde Bash no pasa por `PreToolUse`. El `Stop` lo detecta al final del turno: compara la fecha de cada archivo cambiado del repo fuente con el inicio de la sesión (primer mensaje del transcript). Así, tus cambios sin commitear en `ment-it-questions` no hacen que el agente intente revertirlos.
- **Bucles:** si `Stop` ya bloqueó una vez seguida, no vuelve a bloquear. Los problemas quedan a la vista.

## `quizfmt/`: una sola implementación de la convención

El parser lo usan el sync y los hooks de `ment-it-questions`, que lo importan desde `../quiz-app`. Así, lo que valida el hook al escribir es exactamente lo que entra a la DB. Está protegido: si la convención cambia, la cambia la persona, y luego se actualizan la skill `quiz-format` y `docs/vision.md`.

## Límites conocidos

- Los revisores son probabilistas. La persona sigue siendo la última barrera.
- Para endurecer un revisor, cambia `model:` en su frontmatter (por ejemplo, a `opus`).
