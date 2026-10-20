import type { Catalog, Mode, Order, Stretch } from "../api/client";

/** Lo que la persona elige en la pantalla de inicio. */
export interface Setup {
  mode: Mode;
  topic: string;
  topics: string[];
  area: string;
  tags: string[];
  /** `null` = todas. */
  n: number | null;
  order: Order;
}

export const MODES: { id: Mode; label: string; hint: string }[] = [
  { id: "tema", label: "Un tema", hint: "Todo React, todo Node…" },
  { id: "aleatoria", label: "Mezcla", hint: "Varios temas al azar" },
  { id: "especializada", label: "Especialidad", hint: "Un área o tags concretos" },
  { id: "entrevista", label: "Entrevista", hint: "Por fases, como la real" },
  { id: "reales", label: "Reales", hint: "Las que te han preguntado" },
];

export const ORDERS: { id: Order; label: string }[] = [
  { id: "random", label: "Al azar" },
  { id: "frecuentes-primero", label: "Frecuentes primero" },
  { id: "en-orden", label: "En orden" },
];

/** Las fases de una entrevista (docs/vision.md). */
export const INTERVIEW_PHASES: Stretch[] = [
  { tags: ["fundamentos"], n: 5 },
  { area: "backend", n: 5 },
  { tags: ["diseno"], n: 3 },
  { area: "hr", n: 2 },
];

export function phaseLabel(s: Stretch): string {
  const parts = [s.area, ...(s.tags ?? []), s.topic, ...(s.topics ?? [])].filter(Boolean);
  return `${parts.join(" · ")}${s.n ? ` (${s.n})` : ""}`;
}

/** ¿Hay algo en el catálogo que este tramo pueda encontrar? */
export function phaseExists(s: Stretch, catalog: Catalog): boolean {
  if (s.area && !catalog.areas.some((a) => a.slug === s.area)) return false;
  const tags = s.tags ?? [];
  return tags.length === 0 || tags.some((t) => catalog.tags.some((c) => c.slug === t));
}

export function interviewPlan(catalog: Catalog): Stretch[] {
  return INTERVIEW_PHASES.filter((p) => phaseExists(p, catalog));
}

export function buildPlan(setup: Setup, catalog: Catalog): Stretch[] {
  const base = { n: setup.n, order: setup.order };
  switch (setup.mode) {
    case "tema":
      return [{ ...base, topic: setup.topic }];
    case "aleatoria":
      return [{ ...base, topics: setup.topics }];
    case "especializada":
      return [{ ...base, area: setup.area || null, tags: setup.tags }];
    case "entrevista":
      return interviewPlan(catalog);
    case "reales":
      return [{ ...base, tags: ["real"] }];
  }
}

/** Por qué todavía no se puede empezar, o `null` si ya se puede. */
export function problemWith(setup: Setup, catalog: Catalog): string | null {
  switch (setup.mode) {
    case "tema":
      return setup.topic ? null : "Elige un tema";
    case "aleatoria":
      return setup.topics.length >= 2 ? null : "Elige al menos dos temas";
    case "especializada":
      return setup.area || setup.tags.length ? null : "Elige un área o algún tag";
    case "entrevista":
      return interviewPlan(catalog).length ? null : "Aún no hay preguntas para las fases";
    case "reales":
      return catalog.tags.some((t) => t.slug === "real") ? null : "Aún no hay preguntas reales";
  }
}
