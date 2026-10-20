# Harness: cómo trabajan los agentes en este repo

## Principio

Analogía: un edificio de oficinas.

| Pieza | En el edificio | Cuándo entra en contexto | Qué contiene aquí |
|---|---|---|---|
| `CLAUDE.md` | Directorio del vestíbulo | Siempre | Mapa corto (~25 líneas) |
| `.claude/rules/*.md` con `paths:` | Letrero en la puerta de cada piso | Al leer o editar archivos de esa carpeta | Reglas de backend, sync, frontend y docker |
| Skills | Manual en el archivero | Descripción siempre; cuerpo solo al usarla | `quiz-format`, `convert-batch` |
| Hooks | Torniquetes | Siempre, y no dependen del modelo | Protección, validación, linters, tests |

**Regla para decidir:** ¿se necesita en todas las sesiones? Va en `CLAUDE.md`. ¿Solo al tocar ciertos archivos? Va en una regla con `paths`. ¿Es un procedimiento que se ejecuta a veces? Es una skill. ¿Tiene que cumplirse siempre? Es un hook. `CLAUDE.md` es contexto, no una restricción.

## Agentes

```
                 ┌──────────────────────────────┐
                 │ AGENTE PRINCIPAL             │
                 │ sync → backend → frontend,   │
                 │ en secuencia (un contrato)   │
                 └──┬─────────────┬──────────┬──┘
     /convert-batch │             │          │ tras cambios visibles
                    ▼             ▼          ▼
         question-converter  quiz-reviewer  ux-reviewer
         escribe quiz/       solo lectura   solo lectura + Bash
         skill: quiz-format  skill: quiz-format  (Playwright, Lighthouse)
```

| Subagente | Por qué es un subagente |
|---|---|
| `question-converter` | Tarea independiente y repetitiva. Se queda con la prosa larga del fuente, que si no llenaría el contexto del principal, y devuelve solo keys |
| `quiz-reviewer` | Verificación imparcial: no vio la generación y no puede escribir, así que solo dictamina |
| `ux-reviewer` | Verificación imparcial: quien escribió la UI no califica su propia UX |

- Todos llevan `omitClaudeMd: true`: reciben su contexto por `skills:` o por su propio prompt, y no se contaminan con el del principal.
- **Backend, sync y frontend no se delegan.** Los une un contrato (formato del md → modelo → API → tipos del front). Con un agente por capa, cada traspaso perdería contexto y multiplicaría el costo.

## Hooks

| Evento | Script | Qué hace |
|---|---|---|
| `PreToolUse` (Write, Edit, MultiEdit, NotebookEdit) | `protect_paths.py` | Bloquea escrituras en el repo fuente, `.claude/hooks/`, `.claude/settings.json` y `quizfmt/` |
| `PostToolUse` (Write, Edit, MultiEdit) | `post_edit.py` | `quiz/*.md` → convención; `.py` de backend/sync → `ruff`; `.ts(x)` del frontend → `eslint` |
| `Stop` | `stop_check.py` | Todo el quiz, repo fuente sin cambios, `import-linter`, `tsc --noEmit`, y `pytest` si hay cambios en backend/sync |

- Si una herramienta todavía no existe (scaffolding a medio hacer), el hook la omite sin bloquear.
- **El hueco de Bash:** un `sed -i` desde Bash no pasa por `PreToolUse`. El `Stop` lo detecta al final del turno (cambios en el repo fuente, quiz inválido).
- **Bucles:** si `Stop` ya bloqueó una vez seguida, no vuelve a bloquear. Los problemas quedan a la vista.
- **Protección extra recomendada en tu host:** `chmod -R a-w ../ment-it-questions` cuando no lo estés editando tú.

## `quizfmt/`: una sola implementación de la convención

El parser lo usan los hooks y el sync. Así, lo que valida el hook es exactamente lo que entra a la DB. Está protegido: si la convención cambia, la cambia la persona, y luego se actualizan la skill `quiz-format` y `docs/vision.md`.

## Límites conocidos

- Los revisores son probabilistas. La persona sigue siendo la última barrera.
- Para endurecer un revisor, cambia `model:` en su frontmatter (por ejemplo, a `opus`).
