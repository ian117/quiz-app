---
paths:
  - "frontend/**"
---

# Frontend (React)

Es un juego: la UX es la prioridad, y tiene que ser rápido antes que bonito.

- Vite + React + TypeScript, como SPA (no hace falta SSR).
- **Tipos de la API generados del OpenAPI** del backend (`openapi-typescript`). No escribas a mano los tipos de la API: si el back cambia el esquema, el front debe dejar de compilar.
- **Presupuesto:** Lighthouse Performance ≥ 90 en móvil y JS inicial ≤ 200 KB gzip.
- Animaciones solo con `transform` y `opacity`, respetando `prefers-reduced-motion`.
- Jugable con teclado (`1`-`4` para elegir, `Enter` para seguir) y pensado primero para móvil.
- Contenido enriquecido: la pregunta y la explicación son markdown (código, tablas). Se renderizan con resaltado de sintaxis cargado de forma diferida.
- **La librería de componentes y la de animación están pendientes de decidir.** Pregunta a la persona antes de instalar cualquiera.
- Hooks: `eslint` al editar; `tsc --noEmit` en el hook `Stop`.
- Después de un cambio visible, pide una revisión al subagente `ux-reviewer`.
