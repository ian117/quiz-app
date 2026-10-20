import { describe, expect, it } from "vitest";

import type { AnswerOut, QuestionOut } from "../api/client";
import { averageMs, firstUnanswered, optionIndexForKey, streaks } from "./game";

function q(id: number, result?: boolean, time_ms = 1000): QuestionOut {
  const answer: AnswerOut | null =
    result === undefined
      ? null
      : { question_id: id, option_id: 1, is_correct: result, correct_option_id: 1, explanation_md: "", time_ms };
  return { id, key: `k${id}`, topic: "react", position: id, prompt_md: "", tags: [], options: [], answer };
}

describe("firstUnanswered", () => {
  it("devuelve la primera sin responder", () => {
    expect(firstUnanswered([q(1, true), q(2, false), q(3)])).toBe(2);
  });
  it("devuelve la longitud si ya están todas", () => {
    expect(firstUnanswered([q(1, true), q(2, true)])).toBe(2);
  });
});

describe("streaks", () => {
  it("cuenta la actual y la mejor", () => {
    const qs = [q(1, true), q(2, true), q(3, true), q(4, false), q(5, true), q(6)];
    expect(streaks(qs)).toEqual({ current: 1, best: 3 });
  });
  it("un fallo reinicia la actual", () => {
    expect(streaks([q(1, true), q(2, false)])).toEqual({ current: 0, best: 1 });
  });
});

describe("averageMs", () => {
  it("promedia solo las respondidas", () => {
    expect(averageMs([q(1, true, 1000), q(2, false, 3000), q(3)])).toBe(2000);
  });
  it("es 0 sin respuestas", () => {
    expect(averageMs([q(1)])).toBe(0);
  });
});

describe("optionIndexForKey", () => {
  it("mapea 1-9 al índice si existe la opción", () => {
    expect(optionIndexForKey("1", 4)).toBe(0);
    expect(optionIndexForKey("4", 4)).toBe(3);
    expect(optionIndexForKey("5", 4)).toBeNull();
  });
  it("ignora otras teclas", () => {
    expect(optionIndexForKey("0", 4)).toBeNull();
    expect(optionIndexForKey("a", 4)).toBeNull();
    expect(optionIndexForKey("12", 4)).toBeNull();
  });
});
