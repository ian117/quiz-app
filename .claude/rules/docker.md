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
4. `web`: arranca cuando `api` está sana (`service_healthy`).

- `sync` y `api` usan la misma imagen (`quiz-app-backend`); cambia el comando.
- `api` publica su puerto solo en `127.0.0.1` y tiene healthcheck en `/health`.
- `web` compila el front (Node) y lo sirve con nginx; publica su puerto solo en `127.0.0.1:5173`, el origen que permite el CORS de la API. La URL de la API la usa el navegador, así que `VITE_API_URL` se fija al compilar la imagen.
- `quiz/` se monta en `sync` como `/quiz:ro`.
- **El repo fuente y `~/.ssh` nunca se montan ni se copian en imágenes.** Solo los usan los agentes, en el host.
- El volumen de la DB guarda también el historial, que no se puede reconstruir: no documentes `down -v` como algo rutinario.
- Re-sincronizar a mano: `docker compose run --rm sync`.
- Límite de la máquina: Docker tiene 8 GB. Usa imágenes slim/alpine.
