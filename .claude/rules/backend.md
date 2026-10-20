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
- Postgres; migraciones con Alembic.

## Herramientas que esperan los hooks

`ruff` (al editar), y en el hook `Stop`: `lint-imports` y `pytest -q -x` en `backend/tests/`. Instálalas en `backend/.venv` o en el PATH.

## Tests

- Unitarios para `domain` y `application`, con repositorios en memoria.
- De integración para `infrastructure` y `api`, contra el Postgres de `docker compose`.
