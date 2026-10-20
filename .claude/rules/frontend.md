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
- **Decidido:** Tailwind v4 con componentes propios (sin librería de UI) y Motion con `LazyMotion` para animar (`m`, nunca `motion`). Pregunta antes de añadir otra librería de UI o de animación.
- Los tipos salen de `npm run gen:api` (`--default-non-nullable false`, para que los campos con valor por defecto sean opcionales al enviar). TypeScript se queda en 5.x mientras `openapi-typescript` (peer `^5`) no soporte la 6.
- El JS inicial solo lleva el inicio: el juego (`Play`), el historial, el markdown y el resaltado son chunks diferidos. No importes `react-markdown` ni `highlight.js` fuera de ellos.
- Hooks: `eslint` al editar; `tsc --noEmit` en el hook `Stop`.
- Después de un cambio visible, pide una revisión al subagente `ux-reviewer`.
