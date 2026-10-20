# Visión: app de quiz sobre `ment-it-questions`

Visión general del proyecto. Hay una copia idéntica en el proyecto de Claude (`contexto-quiz-app.md`), que complementa `contexto-plan-aprendizaje.md`.

**Qué va en cada sitio**
- **Este documento:** visión, decisiones y su porqué.
- **`CLAUDE.md`:** solo un mapa corto (qué es, dónde está cada cosa, cómo se levanta).
- **`docs/harness.md`:** cómo trabajan los agentes, las reglas, las skills y los hooks.
- **Contrato (OpenAPI de FastAPI):** solo la API entre back y front.

## Objetivo

Un juego de opción múltiple, para uso personal y sin login, para practicar las preguntas de entrevista del repo privado [ian117/ment-it-questions](https://github.com/ian117/ment-it-questions).

**Lo más importante es el modelo de datos.** Los modos de juego, el historial y las estadísticas futuras son consultas sobre él. Analogía: una biblioteca de música bien etiquetada. Si cada canción tiene bien puestos el género y el artista, cualquier playlist es solo un filtro.

## Repo fuente (verificado el 19 oct 2026)

### Estructura

Está clasificado por carpetas: `<categoria>/<area>/`. Las categorías son `frontend`, `backend`, `cloud`, `ai`, `fundamentos`, y además `hr` en `real-interviews`.

| Carpeta | Preguntas | Formato |
|---|---|---|
| `100-interview-questions/` (14 archivos) | ~625 | `### N. ¿Pregunta? ⭐` o `#### N.` + respuesta en prosa, a veces con código y analogía. Agrupadas en `## Sección N: <subtema>` |
| `real-interviews/` (37 archivos) | 182 | `### Pregunta` + `- Empresa / fecha:` + `- Respuesta:`. **106 respuestas están "por completar"** y no se pueden convertir todavía |

Preguntas por archivo de `100-interview-questions`: Testing 77, AI Eng 61 (+4 en fundamentos), AWS 58, Node 53, JavaScript 50, Next.js 50, Python 50, FastAPI 46, React 46 (+6 ejercicios de live coding), RAG 45, Estilos CSS 33, LangChain 29, Arquitectura 23.

### Reglas que ya tiene el repo fuente

- `100-interview-questions/`: solo la convención de nombres (`<categoria>/<area>/preguntas-entrevista-<tema>.md`) y `_plantilla.md`. **No hay regla para las marcas.** La plantilla no usa números ni leyenda; los archivos reales se fueron alejando de ella.
- `real-interviews/`: las entradas nuevas se agregan al final del archivo del tema (pregunta, empresa/fecha, máximo 4 puntos de respuesta).

### Qué significa el ⭐: frecuencia, no importancia ni dificultad

Cada archivo trae su propia leyenda, y **no son uniformes**:

| Archivos | Leyenda |
|---|---|
| La mayoría | ⭐ = "sale en casi todas las entrevistas" |
| JavaScript, Estilos, Arquitectura | Además 🎯 = "punto que distingue a un senior" |
| AWS | ⭐⭐⭐ casi seguro sale · ⭐⭐ común · ⭐ te diferencia (avanzado). **Aquí una sola estrella significa lo contrario** |
| Testing | 🔥 muy frecuente · 🟢 básica · 🟡 intermedia · 🔴 avanzada |
| AI Engineering | Sin marcas |

**El orden dentro de cada archivo es temático, por sección, no por importancia.** Las preguntas con ⭐ están repartidas por todo el archivo.

## Regla de normalización (decidida)

**Principio: se mapea por significado, no por símbolo.** El `question-converter` lee primero la leyenda de cada archivo y traduce según lo que dice. El mismo símbolo puede significar cosas distintas (el ⭐ de AWS).

| Significado en la leyenda | Tag en el quiz | Casos actuales |
|---|---|---|
| Sale casi siempre | `frecuente` | ⭐ (leyenda general), ⭐⭐⭐ (AWS), 🔥 (Testing) |
| Distingue a un senior / te diferencia | `senior` | 🎯, ⭐ (AWS) |
| Común, sin más | ninguno | ⭐⭐ (AWS) |
| Dificultad | ninguno | 🟢🟡🔴 (Testing) |
| Sección del archivo | tag de subtema | `## Sección 2: Hooks` → `hooks` |
| Viene de `real-interviews/` | `real` | Todas las de esa carpeta |

**Por qué:**
- **`frecuente` se reserva para "casi siempre".** Si también incluyera "común", `frecuentes-primero` dejaría de distinguir: en AWS el 91% de las preguntas quedarían como frecuentes.
- **La dificultad se descarta** porque la decisión es practicar todas. 🔴 dice "difícil", no "distingue a un senior", así que no se convierte en `senior`.
- **Sin leyenda, sin tags de frecuencia** (como AI Engineering): no se adivina. Los tags de subtema sí se ponen.
- **Leyenda nueva o desconocida en el futuro:** el converter no inventa una equivalencia. La reporta y decide la persona; luego se añade una fila a esta tabla y a la skill `quiz-format`.
- **El validador rechaza tags de dificultad o importancia inventados** (`importante`, `avanzada`…), así que un agente no puede saltarse la regla.
- Los ejercicios de live coding quedan fuera del MVP, porque no son de opción múltiple.

## Flujo

```
ment-it-questions (privado)        repo quiz-app
  prosa ──agentes (Claude Code)──▶  quiz/<categoria>/<tema>.md ──sync──▶ Postgres ──FastAPI──▶ React
  en el host                        fuente de verdad del quiz          volumen     sesiones y   juego
                                                                       Docker      calificación
```

1. **Conversión, fuera de Docker:** los agentes leen la prosa y escriben `quiz/`. Corre en Claude Code, en el host, con `/convert-batch`.
2. **Markdown = fuente de verdad del quiz.** `quiz/` replica la clasificación del repo fuente: `quiz/frontend/react.md` da `area=frontend` y `topic=react`.
3. **`sync`:** es otro adaptador de entrada del backend, no un proyecto aparte. El caso de uso `SyncQuiz` (en `application/`) usa el puerto `QuizSource`, que `infrastructure/quiz_source.py` implementa con `quizfmt` (parsea y valida), y la entrada es `app/cli/sync.py`. Hace upsert por `key`. Lo que ya no está se marca como retirado (no se borra). Es idempotente. Corre al levantar compose y también a mano con `docker compose run --rm sync`.
4. **Backend FastAPI:** capas/hexagonal y SQLAlchemy 2.0 con mapper. Arma las sesiones, registra las respuestas y califica. Es el dueño del esquema (modelos ORM y migraciones de Alembic).
5. **Frontend React:** gamificado, rápido y con un look moderno.

## Convención del markdown del quiz

La implementación es `quizfmt/` y el detalle para los agentes está en la skill `quiz-format`.

```md
## react-virtual-dom
¿Qué es el Virtual DOM?
tags: frecuente, fundamentos

- [x] Una copia en memoria del DOM que React compara para aplicar solo los cambios mínimos
- [ ] Un DOM paralelo que el navegador renderiza en otro hilo para que React no bloquee la UI
- [ ] Una caché del HTML ya renderizado que evita volver a pedir la página al servidor
- [ ] El DOM real sin sus eventos, lo que lo hace más ligero y rápido de actualizar

> Explicación: React compara el árbol nuevo con el anterior (diffing) y solo toca lo que cambió.
```

- `## key`: `<tema>-<concepto>`, un slug estable y único. **Es el ID del markdown**, como una CURP: nunca cambia ni se reutiliza. No se usan números, porque insertar una pregunta obligaría a renumerar.
- **Pregunta:** todo lo que hay entre `##` y la primera opción. La primera línea es el texto; luego admite código, tablas e imágenes (markdown estándar).
- `tags:` es opcional y es la única clasificación por pregunta. Sigue la regla de normalización. No hay campos fijos como dificultad.
- Exactamente un `[x]` y al menos tres `[ ]`. La correcta no puede ser la más larga, salvo cuando todas las opciones son cortas (≤ 20 caracteres).
- **Explicación:** todo el bloque `>` (varias líneas, con código).
- **Orden e inserción:**
  - El converter conserva el orden del archivo fuente.
  - Una pregunta nueva va en la zona de su subtema, o al final.
  - Es seguro insertar en medio: la identidad es la `key` y `position` lo recalcula el `sync`.

## Modelo de datos (Postgres)

```
topic(id, slug, name, area)
question(id, key UNIQUE, topic_id FK, position, prompt_md, explanation_md, retired_at)
option(id, question_id FK, text_md, is_correct, retired_at)    UNIQUE (question_id, text_md)
tag(id, slug)                 question_tag(question_id FK, tag_id FK)        muchos a muchos
session(id, mode, plan JSON, started_at, finished_at, score, total)
session_question(session_id FK, question_id FK, position)                     qué preguntas salieron
answer(id, session_id FK, question_id FK, option_id FK, is_correct, time_ms)  qué respondiste
```

- `id` numérico interno para las foreign keys; `key` es la identidad estable que viene del markdown.
- **"Retirar, nunca borrar"** mantiene intacto el historial: una pregunta retirada sigue existiendo para las sesiones pasadas.
- **Las opciones siguen la misma regla.** La identidad de una opción es `(question_id, text_md)`, con `UNIQUE`:
  - Si el texto no cambia, se actualiza `is_correct` en la misma fila.
  - Si cambia, se crea una fila nueva y la vieja se retira (`retired_at`).
  - Si un texto retirado vuelve, se reactiva.
  - Nunca se borran opciones, así que `answer.option_id` siempre apunta a una fila que existe, con el texto que se vio.
- **Orden de las opciones (decidido):** `option` no guarda orden y en el markdown la correcta va primero, así que el backend baraja al servir.
  - El orden es una función pura de `(session_id, question_id)` y de la identidad de cada opción: `shuffle_option_ids` en `domain/shuffle.py`.
  - Cada opción se ordena por el SHA-256 de `sesión:pregunta:opción`. No se usa `random` ni `hash()`, porque no son estables entre versiones o procesos.
  - `GET /sessions/{id}` muestra el mismo orden siempre, sin guardar nada. No hay `position` en `option`.
  - No depende del orden de entrada, y retirar una opción no mueve a las demás.
  - Cambiar el algoritmo reordena el historial: un test fija órdenes concretos para avisarlo.
- `answer` lleva una FK compuesta a `session_question (session_id, question_id)` y `UNIQUE (session_id, question_id)`: solo se responde lo que salió en la sesión, y una vez.
- `session_question` existe porque `answer` solo guarda lo respondido. Sin ella, una sesión abandonada pierde qué preguntas salieron.
- **Sin login ni puntaje persistente:** el historial (`session` + `session_question` + `answer`) es el único registro. Las estadísticas futuras (las más falladas, las que nunca han salido) son consultas, sin cambiar el modelo.

## Modos de juego = una sesión hecha de tramos

Cada tramo es `{filtro, n, orden}`. Todos los modos se describen con la misma estructura:

| Modo | Plan |
|---|---|
| Tema o tecnología | `[{topic: react, n: todas, order: random}]` |
| Aleatoria enumerada | `[{topics: [react, node], n: 10}]` |
| Especializada | `[{area: frontend, n: 15}]` o `[{tags: [hooks], n: 8}]` |
| Entrevista por fases | `[{tags: [fundamentos], n: 5}, {area: backend, n: 5}, {tags: [diseno], n: 3}, {area: hr, n: 2}]` |
| Entrevistas reales | `[{tags: [real], n: 10}]` |

- **Orden** (`order`): `random` (por defecto) · `en-orden` (por `position`, el orden temático del archivo) · `frecuentes-primero` (las que tienen el tag `frecuente`, luego el resto al azar).
- **Las fases son tags** (`fundamentos`, `diseno`, `conductual`). La especialidad sale del área. No se añaden columnas.

### API

- `GET /catalog`: áreas, temas y tags, con cuántas preguntas activas tiene cada uno. El front muestra "hay 46" y te deja elegir cuántas (todas por defecto).
- `POST /sessions`: recibe el plan, elige las preguntas, guarda `session_question` y las devuelve **sin marcar la correcta** y con las opciones barajadas (ver "Orden de las opciones").
- `POST /sessions/{id}/answers`: registra la respuesta, califica y devuelve si acertaste y la explicación.
- `GET /sessions`, `GET /sessions/{id}`: historial.
- `GET /health`: para el healthcheck de compose; no es parte del juego.

**El contrato es `backend/openapi.json`**, exportado de la app (`python -m app.api.openapi`). Un test falla si el código y el archivo se desvían, y de ahí salen los tipos del front.

### Reglas de la API (decididas)

- **El plan.** `POST /sessions` recibe `{mode, plan}`:
  - `mode` es uno de `tema`, `aleatoria`, `especializada`, `entrevista`, `reales`.
  - `plan` es una lista de 1 a 20 tramos `{topic, topics, area, tags, n, order}`.
  - `n` ausente o `null` significa todas.
  - Se rechazan las claves desconocidas.
- **Filtros de un tramo.** AND entre claves distintas y OR dentro de una lista: `{area: backend, tags: [a, b]}` es "backend Y (a O b)". Para exigir los dos tags habría que cambiar el contrato.
- **Qué preguntas salen.** Solo las activas (`retired_at` nulo).
- **Una pregunta no se repite entre tramos:** cada tramo excluye lo que ya salió.
- **Un tramo con menos preguntas de las pedidas** aporta las que haya, y `session.total` refleja la cifra real. Si el plan entero no encuentra nada, responde 422.
- **Qué opciones se ven.** Al crear la sesión, solo las activas. Al consultarla (`GET /sessions/{id}`), las activas, más la que se respondió aunque se haya retirado después. `option` no guarda cuándo se creó, así que no se puede reconstruir exactamente "las opciones de aquel día".
- **Cierre.** `finished_at` se pone al responder la última pregunta. Una sesión abandonada queda abierta, sin endpoint para cerrarla.
- **Errores.** Sesión inexistente: 404. Responder dos veces la misma pregunta: 409. Pregunta que no salió en la sesión, opción de otra pregunta, plan sin preguntas o cuerpo inválido: 422.
- **Qué revela cada respuesta.** Solo `answer` (la respuesta dada, `is_correct`, `correct_option_id` y la explicación) lleva la correcta. Una pregunta sin responder no tiene esos campos en el schema.
- **Límite conocido:** los ids de las opciones se asignan al crearlas y la correcta va primera en el markdown, así que un cliente tramposo podría deducir que la de menor id es la correcta. Para uso personal se acepta; cerrarlo exigiría cambiar el contrato (responder por posición, no por id).
- **Stack.** SQLAlchemy síncrono (los endpoints son `def`, FastAPI los corre en un pool de hilos). Los endpoints que escriben hacen `commit` de forma explícita; sin commit, al cerrar la sesión se descarta todo. CORS solo para los orígenes de `CORS_ORIGINS` (por defecto, el Vite local).

Como el backend registra las respuestas, también califica. Se resuelve gratis el trade-off anterior de mandar la correcta al front.

## Frontend: rápido primero, bonito después

- Vite + React como SPA: no necesita SSR.
- Presupuesto medible: Lighthouse Performance ≥ 90 en móvil y JS inicial ≤ 200 KB gzip, revisado por `ux-reviewer`.
- Animaciones ligeras, solo con `transform` y `opacity`.
- Gamificación visual dentro de la sesión (racha, feedback inmediato), sin cuentas.
- Tipos generados del OpenAPI.
- **Decidido:** Tailwind v4 con componentes propios y Motion (`LazyMotion`, ~18 KB gzip diferidos). Pocas pantallas y presupuesto estricto: una librería de UI no se paga sola. Para el router, `#/` a mano (inicio, `#/play/:id`, `#/history`): no hace falta una dependencia.
- Markdown y resaltado (`react-markdown` + `highlight.js` con solo los lenguajes comunes) y las pantallas de juego e historial son chunks diferidos; el JS inicial queda en unos 88 KB gzip (medido sobre lo que sirve nginx).

## Infraestructura local: `docker compose up`

| Servicio | Qué hace | Arranca cuando |
|---|---|---|
| `db` | Postgres con sus datos en un volumen nombrado | Primero, con healthcheck |
| `sync` | Job de un solo uso, con la imagen del backend: `alembic upgrade head && python -m app.cli.sync`. Lee `quiz/` (montado `:ro`), hace upsert y termina | `db` sano |
| `api` | FastAPI, con la imagen del backend; healthcheck en `/health`; puerto solo en localhost | `sync` terminó bien |
| `web` | React | `api` arriba |

- **Las preguntas en la DB son desechables:** se reconstruyen desde `quiz/`. **El historial no**, así que el volumen se protege y se respalda. Nada de `down -v` sin respaldo.
- **El repo fuente no entra a Docker.** Se clona en el host con la SSH que ya funciona (`git clone git@github.com:ian117/ment-it-questions.git ../ment-it-questions`). Así no hay llaves en imágenes ni hay que reconstruir para actualizar.
- Docker tiene como máximo 8 GB: los cuatro servicios caben de sobra.

## Decisiones tomadas

- Sin login, un solo jugador. Sin dificultad como campo fijo: la idea es practicar todas.
- Repo nuevo `quiz-app`, separado del fuente. Postgres en Docker.
- Clasificación: carpeta/archivo (área y tema) + `tags:` por pregunta, con la regla de normalización de arriba.
- El backend arma las sesiones, registra las respuestas y califica (deja de ser de solo lectura).
- MVP: un tema (React, 46 preguntas conceptuales).
- **Harness aplicado** (detalle en `docs/harness.md`):
  - `CLAUDE.md` corto.
  - Reglas por carpeta con `paths`.
  - Skills `quiz-format` (precargada en los subagentes) y `convert-batch` (solo la invoca la persona).
  - Subagentes `question-converter`, `quiz-reviewer` y `ux-reviewer`, con `omitClaudeMd`.
  - Hooks `PreToolUse`, `PostToolUse` y `Stop`.
- **Preferencias personales** (español, breve, analogías, explicar el porqué, preguntar antes de decidir) en `~/.claude/CLAUDE.md`. No hay procedimiento de cierre con preguntas de entrevista: aquí se practica usando la app.

## Pendiente de decidir

| Tema | Recomendación |
|---|---|
| Preguntas reales "por completar" (106) | Se convierten cuando tengan respuesta |
| Opcional: actualizar `_plantilla.md` del repo fuente | Que documente la numeración y una leyenda única. Ayudaría a que las marcas sean uniformes en el futuro |

## Siguiente paso (en el host)

1. Lotes de React con `/convert-batch react 1-10`, y así sucesivamente.
2. ~~`docker-compose.yml` + `sync` + el modelo de datos.~~ Hecho (el sync vive en `backend/`).
3. ~~Backend: la API sobre el mismo esquema.~~ Hecho (`api` en compose; contrato en `backend/openapi.json`).
4. ~~Frontend.~~ Hecho (`web` en compose; ver "Frontend").
