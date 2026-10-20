import type { Mode } from "../api/client";

export const MODE_LABEL: Record<Mode, string> = {
  tema: "Un tema",
  aleatoria: "Mezcla",
  especializada: "Especialidad",
  entrevista: "Entrevista",
  reales: "Reales",
};

const dateFormat = new Intl.DateTimeFormat("es", { dateStyle: "medium", timeStyle: "short" });

export function formatDate(iso: string): string {
  // La API manda datetimes sin zona: son UTC.
  const hasZone = /(Z|[+-]\d{2}:?\d{2})$/.test(iso);
  return dateFormat.format(new Date(hasZone ? iso : `${iso}Z`));
}

export function formatSeconds(ms: number): string {
  return `${(ms / 1000).toFixed(1)} s`;
}

export function percent(score: number, total: number): number {
  return total ? Math.round((score / total) * 100) : 0;
}
