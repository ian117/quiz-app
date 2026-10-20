import createClient from "openapi-fetch";

import type { components, paths } from "./schema";

type Schemas = components["schemas"];

export type Catalog = Schemas["CatalogOut"];
export type Mode = Schemas["Mode"];
export type Order = Schemas["Order"];
export type Stretch = Schemas["StretchIn"];
export type SessionOut = Schemas["SessionOut"];
export type SessionSummary = Schemas["SessionSummaryOut"];
export type QuestionOut = Schemas["QuestionOut"];
export type AnswerOut = Schemas["AnswerOut"];
export type AnswerResult = Schemas["AnswerResultOut"];

export const api = createClient<paths>({
  baseUrl: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
});

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function detailOf(error: unknown): string | null {
  if (typeof error !== "object" || error === null || !("detail" in error)) return null;
  const { detail } = error;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d: { msg?: string }) => d.msg ?? "").join("; ");
  return null;
}

/** Devuelve `data` o lanza `ApiError` (también si no hay red). */
export async function unwrap<T>(
  request: Promise<{ data?: T; error?: unknown; response: Response }>,
): Promise<T> {
  let result;
  try {
    result = await request;
  } catch {
    throw new ApiError(0, "No se pudo conectar con la API. ¿Está levantada (docker compose up)?");
  }
  if (result.data === undefined) {
    const { status } = result.response;
    throw new ApiError(status, detailOf(result.error) ?? `La API respondió ${status}`);
  }
  return result.data;
}
