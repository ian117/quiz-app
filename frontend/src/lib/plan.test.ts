import { describe, expect, it } from "vitest";

import type { Catalog } from "../api/client";
import { buildPlan, interviewPlan, problemWith, type Setup } from "./plan";

const catalog: Catalog = {
  areas: [{ slug: "frontend", question_count: 10 }],
  topics: [{ slug: "react", name: "React", area: "frontend", question_count: 10 }],
  tags: [
    { slug: "frecuente", question_count: 7 },
    { slug: "fundamentos", question_count: 10 },
  ],
};

const base: Setup = {
  mode: "tema",
  topic: "react",
  topics: [],
  area: "",
  tags: [],
  n: 10,
  order: "random",
};

describe("buildPlan", () => {
  it("un tema es un solo tramo", () => {
    expect(buildPlan(base, catalog)).toEqual([{ n: 10, order: "random", topic: "react" }]);
  });

  it("«todas» manda n null", () => {
    expect(buildPlan({ ...base, n: null }, catalog)[0]?.n).toBeNull();
  });

  it("especializada sin área manda null", () => {
    const plan = buildPlan({ ...base, mode: "especializada", tags: ["frecuente"] }, catalog);
    expect(plan).toEqual([{ n: 10, order: "random", area: null, tags: ["frecuente"] }]);
  });

  it("reales filtra por el tag real", () => {
    expect(buildPlan({ ...base, mode: "reales" }, catalog)[0]?.tags).toEqual(["real"]);
  });
});

describe("interviewPlan", () => {
  it("omite las fases que no existen en el catálogo", () => {
    expect(interviewPlan(catalog)).toEqual([{ tags: ["fundamentos"], n: 5 }]);
  });
});

describe("problemWith", () => {
  it("pide lo que falta en cada modo", () => {
    expect(problemWith({ ...base, topic: "" }, catalog)).toBe("Elige un tema");
    expect(problemWith({ ...base, mode: "aleatoria", topics: ["react"] }, catalog)).toMatch(/dos/);
    expect(problemWith({ ...base, mode: "especializada" }, catalog)).toMatch(/área/);
    expect(problemWith({ ...base, mode: "reales" }, catalog)).toMatch(/reales/);
  });

  it("deja empezar cuando está completo", () => {
    expect(problemWith(base, catalog)).toBeNull();
    expect(problemWith({ ...base, mode: "entrevista" }, catalog)).toBeNull();
  });
});
