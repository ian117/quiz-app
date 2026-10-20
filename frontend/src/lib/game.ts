import type { QuestionOut } from "../api/client";

/** Índice de la primera pregunta sin responder; `questions.length` si ya están todas. */
export function firstUnanswered(questions: QuestionOut[]): number {
  const i = questions.findIndex((q) => !q.answer);
  return i === -1 ? questions.length : i;
}

/** Racha actual (aciertos seguidos hasta la última respondida) y la mejor de la sesión. */
export function streaks(questions: QuestionOut[]): { current: number; best: number } {
  let current = 0;
  let best = 0;
  for (const q of questions) {
    if (!q.answer) break;
    current = q.answer.is_correct ? current + 1 : 0;
    best = Math.max(best, current);
  }
  return { current, best };
}

/** Tiempo medio por pregunta respondida, en ms (0 si no hay ninguna). */
export function averageMs(questions: QuestionOut[]): number {
  const times = questions.flatMap((q) => (q.answer ? [q.answer.time_ms] : []));
  return times.length ? times.reduce((a, b) => a + b, 0) / times.length : 0;
}

/** Tecla `1`-`9` → índice de la opción (o `null`). */
export function optionIndexForKey(key: string, optionCount: number): number | null {
  if (!/^[1-9]$/.test(key)) return null;
  const i = Number(key) - 1;
  return i < optionCount ? i : null;
}
