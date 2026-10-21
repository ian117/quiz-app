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
| `question-converter` | Tarea independiente y repetitiva. Lee el extracto del lote (no el fuente completo), lo convierte y devuelve solo keys |
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

## Costo de la conversión

**Medición (20 oct 2026):** convertir casi todo el quiz en una sola sesión agotó el límite de 5 horas. Fueron 379 llamadas del principal (en Sonnet), unos 70 subagentes, 137 M tokens de `cache_read` y 17.8 M de `cache_creation`. Un 50% fue del principal y otro 50% de los subagentes.

| Causa | Por qué cuesta | Arreglo |
|---|---|---|
| Un principal orquesta todos los lotes | Cada resultado se queda en su contexto, y la llamada N relee las N-1 anteriores: el costo crece al cuadrado | `tools/convert.py`: el bucle es Python y cada lote es un `claude -p` nuevo, con el contexto vacío |
| Cada agente lee el fuente completo (50-77 preguntas) y el destino completo | Unos 100 k tokens por agente solo para arrancar | `tools/extract_batch.py` deja leyenda + lote en `.convert/`; el revisor lee solo sus keys con `Grep` |
| El converter edita pregunta por pregunta | Cada `Edit` es otra llamada que relee todo su contexto | Un solo `Write`/`Edit` por lote; luego solo arreglos puntuales |
| La segunda vuelta revisa el lote entero | Duplica el revisor | Solo se re-revisan las keys en `FAIL` |
| `TELL` se cruzaba con la regla de largo del hook | El revisor reprobaba lo que el hook ya aceptaba, y eso disparaba vueltas | `TELL` ya no juzga el largo |

Analogía: antes, un solo mesero atendía toda la noche y releía todos los tickets del día antes de cada pedido. Ahora cada mesa tiene una comanda nueva.

**Para medir:** `--output-format json` deja `total_cost_usd` por lote en `.convert/<tema>-<a>-<b>.json`, y `convert.py` imprime el total.

## Límites conocidos

- Los revisores son probabilistas. La persona sigue siendo la última barrera.
- Para endurecer un revisor, cambia `model:` en su frontmatter (por ejemplo, a `opus`).
