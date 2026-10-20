---
paths:
  - "docker-compose.yml"
  - "**/Dockerfile"
---

# Docker

`docker compose up` levanta, en orden:

1. `db`: Postgres con un volumen nombrado y healthcheck.
2. `sync`: job de un solo uso que termina; arranca cuando `db` está sano (`service_healthy`).
3. `api`: arranca cuando `sync` terminó bien (`service_completed_successfully`).
4. `web`: arranca cuando `api` está arriba.

- `quiz/` se monta en `sync` como `/quiz:ro`.
- **El repo fuente y `~/.ssh` nunca se montan ni se copian en imágenes.** Solo los usan los agentes, en el host.
- El volumen de la DB guarda también el historial, que no se puede reconstruir: no documentes `down -v` como algo rutinario.
- Re-sincronizar a mano: `docker compose run --rm sync`.
- Límite de la máquina: Docker tiene 8 GB. Usa imágenes slim/alpine.
