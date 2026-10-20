---
paths:
  - "backend/**"
---

# Backend (FastAPI)

Modelo de datos, modos de juego y API: `docs/vision.md` (secciones "Modelo de datos" y "API"). Es el contrato; si hay que cambiarlo, pregunta antes.

## Arquitectura hexagonal

```
backend/app/
  domain/          entidades y reglas puras: sin fastapi, sqlalchemy ni pydantic
  application/     casos de uso + puertos (interfaces de repositorio)
  infrastructure/  SQLAlchemy 2.0 (modelos ORM, mappers dominio<->ORM, repositorios)
  api/             routers FastAPI y schemas Pydantic
```

- La entidad de dominio y el modelo ORM son clases distintas; un mapper explícito convierte entre ambas.
- Las dependencias apuntan hacia dentro. Se hace cumplir con `import-linter` (contratos en `pyproject.toml`): `domain` no importa nada externo; `application` no importa `infrastructure` ni `api`.
- El backend califica: nunca envía `is_correct` antes de que se responda.
- Postgres; migraciones con Alembic. El backend es dueño del esquema (`app/infrastructure/orm/models.py`); el sync y la API lo comparten.
- Las reglas de la API (plan, filtros, errores, qué opciones se ven) están decididas en `docs/vision.md`, sección "Reglas de la API".

## Convenciones

- SQLAlchemy síncrono. Los endpoints son `def` y los que escriben llaman a `db.commit()` ellos mismos (ver `app/api/deps.py`).
- Los casos de uso devuelven vistas de `application/views.py`, que es donde se decide qué se revela: una pregunta sin responder nunca lleva `is_correct`, la correcta ni la explicación.
- El orden de las opciones es `domain/shuffle.py`: cambiarlo reordena el historial (un test lo fija).
- **Si cambias un schema o un endpoint,** regenera el contrato: `cd backend && PYTHONPATH=.:.. .venv/bin/python -m app.api.openapi > openapi.json`. Un test falla si no coincide.
- Las migraciones se generan con `alembic revision --autogenerate` y se revisan; un test comprueba que coincidan con los modelos.

## Herramientas que esperan los hooks

`ruff` (al editar), y en el hook `Stop`: `lint-imports` y `pytest -q -x` en `backend/tests/`. Instálalas en `backend/.venv` o en el PATH.

## Tests

- Unitarios para `domain` y `application`, con repositorios en memoria.
- De integración para `infrastructure` y `api`, contra el Postgres de `docker compose`, en la base aparte `quiz_test` (nunca en `quiz`, que guarda el historial). Cargan los datos con el sync real.
