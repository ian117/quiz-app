---
name: convert-batch
description: Convierte un lote de preguntas del repo fuente al quiz y las revisa de forma imparcial. Ejemplo - /convert-batch react 1-10
argument-hint: <tema> <rango>
disable-model-invocation: true
---

# Convertir un lote: $ARGUMENTS

1. **Ubica el archivo fuente** del tema en `../ment-it-questions/100-interview-questions/<categoria>/<area>/` (o en `real-interviews/<categoria>/<tema>.md` si se pide un lote de entrevistas reales). Si hay más de un candidato o ninguno, pregunta.
2. **Destino:** `quiz/<categoria>/<tema>.md`, con la misma categoría que el fuente.
3. **Invoca `question-converter`** con:
   - la ruta del fuente,
   - el rango pedido (los números del fuente),
   - el destino,
   - y la leyenda del archivo fuente copiada tal cual.

   No le pases nada más de esta conversación.
4. **Invoca `quiz-reviewer`** con el destino, la lista de keys que devolvió el converter y la ruta del fuente. No le cuentes cómo se generaron.
5. **Si hay `FAIL`,** reinvoca `question-converter` solo con esas keys y el detalle del revisor. Máximo 2 vueltas.
6. **Responde a la persona con:**
   - una tabla `key | veredicto final | nota`;
   - las leyendas o marcas que el converter no supo traducir;
   - las preguntas que siguen en `FAIL` después de 2 vueltas, para que decida ella.

No hagas commit: la persona revisa el lote y estudia las preguntas antes.
