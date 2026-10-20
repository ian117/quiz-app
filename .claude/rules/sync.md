---
paths:
  - "backend/app/cli/**"
  - "backend/app/application/sync_quiz.py"
  - "backend/app/domain/catalog.py"
  - "backend/app/infrastructure/quiz_source.py"
  - "backend/app/infrastructure/catalog_repository.py"
  - "backend/tests/**/test_sync*.py"
  - "backend/tests/**/test_catalog.py"
  - "backend/tests/**/test_quiz_source.py"
---

# Sync (quiz/*.md → Postgres)

El sync no es un proyecto aparte: es otro adaptador de entrada del backend (ver `backend.md` para la arquitectura).

- `application/sync_quiz.py`: caso de uso `SyncQuiz`. Puertos en `application/ports.py`: `QuizSource` y `CatalogRepository`.
- `infrastructure/quiz_source.py`: `QuizFileSource`, el adaptador de `QuizSource`. Usa `quizfmt.load_tree()` para leer y validar. No reimplementes el parser: `quizfmt/` es la única implementación de la convención y está protegido.
- `domain/catalog.py`: la regla de reconciliación (`Catalog.reconcile`), pura y sin I/O.
- `infrastructure/catalog_repository.py`: repositorio SQLAlchemy (el mapper dominio↔ORM está en `infrastructure/mappers.py`).
- `cli/sync.py`: la entrada (`python -m app.cli.sync`). Lee `DATABASE_URL` y `QUIZ_DIR` (en Docker, `/quiz`, montado `:ro`).

## Reglas

- Si el quiz es inválido, no toca la DB y termina con código 1.
- **Upsert por `key`.** Área = carpeta, tema = nombre del archivo, `position` = orden en el archivo, tags en la tabla `question_tag`.
- Lo que ya no está en el markdown recibe `retired_at`; si vuelve a aparecer, se reactiva. **Nunca se borra**: el historial apunta a esas filas.
- **Opciones, misma regla.** Su identidad es `(question_id, text_md)`. Si el texto no cambia, se actualiza `is_correct` en la misma fila; si cambia, se crea una fila nueva y la vieja se retira; si un texto retirado vuelve, se reactiva.
- Todo en una sola transacción.
- **Idempotente:** un test corre el sync dos veces y comprueba que el estado de la DB es idéntico.
- El servicio `sync` de compose usa la imagen del backend y ejecuta `alembic upgrade head && python -m app.cli.sync`.

## Tests

- Unitarios (`backend/tests/unit/`): `Catalog.reconcile` y `SyncQuiz` con repositorio en memoria.
- Integración (`backend/tests/integration/`): el sync completo contra el Postgres de compose, en la base aparte `quiz_test` (nunca en `quiz`, que guarda el historial).
- El hook `Stop` ejecuta `pytest` si `backend/` tiene cambios.
