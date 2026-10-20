---
name: quiz-format
description: Convención de los archivos quiz/*.md y regla para traducir las marcas (⭐, 🎯, 🔥) del repo fuente a tags. Úsala al escribir, revisar o sincronizar preguntas del quiz.
user-invocable: false
---

# Convención de quiz/*.md

Ubicación: `quiz/<categoria>/<tema>.md`. Categoría ∈ `frontend, backend, cloud, ai, fundamentos, hr`. Es la misma clasificación que el repo fuente.

```md
# React

## react-virtual-dom
¿Qué es el Virtual DOM?
tags: frecuente, fundamentos

- [x] Una copia en memoria del DOM que React compara para aplicar solo los cambios mínimos
- [ ] Un DOM paralelo que el navegador renderiza en otro hilo para que React no bloquee la UI
- [ ] Una caché del HTML ya renderizado que evita volver a pedir la página al servidor
- [ ] El DOM real sin sus eventos, lo que lo hace más ligero y rápido de actualizar

> Explicación: React compara el árbol nuevo con el anterior (diffing) y solo toca lo que cambió.
```

## Reglas

1. **`## key`:** `<tema>-<concepto>`, un slug. Es el ID: nunca cambia ni se reutiliza. No uses números.
2. **Pregunta:** todo lo que hay entre `##` y la primera opción. La primera línea es el texto de la pregunta; después puede haber código (```` ```lang ````), tablas o listas.
3. **`tags:`** opcional, una sola línea en la zona de la pregunta. Son slugs sin acentos, separados por coma.
4. **Opciones:** exactamente un `- [x]` y al menos tres `- [ ]`, una línea cada una (se permite código inline). El frontend las mezcla, así que pon la correcta primero.
5. **Largo parecido:** la correcta no puede ser la más larga. Se exceptúan las opciones cortas (≤ 20 caracteres, como `1`, `2`, `undefined`).
6. **Distractores:** errores conceptuales plausibles (confusiones típicas, medias verdades, conceptos vecinos). Ninguno puede ser también correcto ni absurdo.
7. **Explicación:** todo el bloque `>`, que empieza con `> Explicación:`. Puede tener varias líneas y código (cada línea con `>`).
8. **Orden e inserción:** conserva el orden del archivo fuente. Una pregunta nueva va en la zona de su subtema, o al final. Es seguro: la identidad es la `key`.

## Traducir marcas a tags: por significado, no por símbolo

Lee primero la `**Leyenda:**` del archivo fuente. El mismo símbolo cambia de significado entre archivos.

| Lo que dice la leyenda | Tag | Casos conocidos |
|---|---|---|
| Sale casi siempre | `frecuente` | ⭐ (leyenda general), ⭐⭐⭐ (AWS), 🔥 (Testing) |
| Distingue a un senior / te diferencia | `senior` | 🎯, ⭐ (AWS, una sola estrella) |
| Común, sin más | ninguno | ⭐⭐ (AWS) |
| Dificultad | ninguno | 🟢 🟡 🔴 (Testing) |

- **Tag de subtema** a partir de la sección del fuente: `## Sección 2: Hooks` → `hooks`. Uno por pregunta, en minúsculas y sin acentos.
- **`real`** para todo lo que venga de `real-interviews/`. Las entradas con respuesta "por completar" no se convierten.
- **Archivo sin leyenda** (como AI Engineering): no hay tags de frecuencia. No adivines.
- **Leyenda nueva o que no está en la tabla:** no inventes una equivalencia. Repórtala en tu respuesta final y deja esas preguntas sin tag de marca.
- Están prohibidos los tags de dificultad o importancia inventados (`importante`, `avanzada`…). El validador los rechaza.
- **Ejercicios de live coding:** no se convierten, porque no son de opción múltiple.

## Validación

Un hook valida cada archivo al escribirlo. A mano: `python3 -m quizfmt`.
