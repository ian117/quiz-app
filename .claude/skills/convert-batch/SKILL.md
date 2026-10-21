---
name: convert-batch
description: Convierte un lote ya extraído del repo fuente al quiz y lo revisa de forma imparcial. Normalmente lo lanza tools/convert.py, un lote por sesión. Ejemplo - /convert-batch .convert/react-1-10.md quiz/frontend/react.md
argument-hint: <extracto> <destino>
disable-model-invocation: true
---

# Convertir un lote: $ARGUMENTS

Tu papel es **coordinar, no leer**. El costo de este flujo depende de que el contexto de cada agente sea pequeño.

1. **Argumentos:** `<extracto>` (`.convert/<tema>-<a>-<b>.md`, con la leyenda y solo las preguntas del lote) y `<destino>` (`quiz/<categoria>/<tema>.md`).
   - Si recibes tema y rango en lugar de un extracto, no busques el fuente tú: dile a la persona que use `python3 tools/convert.py <fuente> <categoria>/<tema> --lotes <rango>` y termina.
   - **No leas el extracto, el fuente ni el destino.** Solo pasa las rutas.
2. **Invoca `question-converter`** con el extracto y el destino. No le pases nada más de esta conversación.
3. **Invoca `quiz-reviewer`** con el extracto, el destino y la lista de keys que devolvió el converter. No le cuentes cómo se generaron.
4. **Si hay `FAIL`,** reinvoca `question-converter` solo con esas keys y el detalle del revisor. Luego reinvoca `quiz-reviewer` **solo con esas keys**. Máximo 2 vueltas.
5. **Responde, breve:**
   - una tabla `key | veredicto final | nota` (nota solo si no es PASS limpio);
   - las leyendas o marcas que el converter no supo traducir;
   - las preguntas que siguen en `FAIL` tras 2 vueltas, para que decida la persona.

No hagas commit y no ejecutes nada más: la persona revisa el lote y estudia las preguntas antes.
