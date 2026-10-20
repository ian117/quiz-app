import { useState } from "react";

import { api, unwrap, type QuestionOut, type SessionOut } from "../api/client";
import { averageMs, streaks } from "../lib/game";
import { formatSeconds, MODE_LABEL, percent } from "../lib/format";
import { go, paths } from "../lib/router";
import { ErrorBox } from "./Status";
import { Markdown } from "./Markdown";

function verdict(pct: number): string {
  if (pct === 100) return "¡Perfecto!";
  if (pct >= 80) return "Muy bien";
  if (pct >= 50) return "Vas por buen camino";
  return "A repasar";
}

function optionText(q: QuestionOut, id: number): string {
  return q.options.find((o) => o.id === id)?.text_md ?? "(opción retirada del quiz)";
}

export function Results({ session }: { session: SessionOut }) {
  const [retrying, setRetrying] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const pct = percent(session.score, session.total);
  const { best } = streaks(session.questions);
  const missed = session.questions.filter((q) => q.answer && !q.answer.is_correct);

  async function retry() {
    setRetrying(true);
    setError(null);
    try {
      const next = await unwrap(api.POST("/sessions", { body: { mode: session.mode, plan: session.plan } }));
      go(paths.play(next.id));
    } catch (e) {
      setError(e as Error);
      setRetrying(false);
    }
  }

  return (
    <section className="flex flex-col gap-6">
      <div className="rounded-2xl border border-line bg-surface p-6 text-center">
        <p className="text-sm text-muted">{MODE_LABEL[session.mode]}</p>
        <p className="mt-1 text-5xl font-bold tabular-nums">{pct}%</p>
        <p className="mt-1 text-lg font-medium">{verdict(pct)}</p>
        <dl className="mt-5 grid grid-cols-3 gap-2 text-sm">
          <div>
            <dd className="text-xl font-semibold tabular-nums">
              {session.score}/{session.total}
            </dd>
            <dt className="text-muted">Aciertos</dt>
          </div>
          <div>
            <dd className="text-xl font-semibold tabular-nums">🔥 {best}</dd>
            <dt className="text-muted">Mejor racha</dt>
          </div>
          <div>
            <dd className="text-xl font-semibold tabular-nums">{formatSeconds(averageMs(session.questions))}</dd>
            <dt className="text-muted">Por pregunta</dt>
          </div>
        </dl>
      </div>

      {error && <ErrorBox error={error} />}

      <div className="flex flex-col gap-2 sm:flex-row">
        <button
          type="button"
          onClick={() => void retry()}
          disabled={retrying}
          className="min-h-12 flex-1 rounded-xl bg-accent px-6 font-semibold text-accent-ink disabled:opacity-40"
        >
          {retrying ? "Preparando…" : "Otra ronda igual"}
        </button>
        <a
          href={paths.home}
          className="grid min-h-12 flex-1 place-items-center rounded-xl border border-line bg-surface px-6 font-semibold"
        >
          Cambiar de modo
        </a>
      </div>

      {missed.length > 0 && (
        <div className="flex flex-col gap-3">
          <h2 className="text-lg font-semibold">Para repasar ({missed.length})</h2>
          {missed.map((q) => (
            <details key={q.id} className="group rounded-xl border border-line bg-surface p-4">
              <summary className="flex cursor-pointer items-start gap-2 font-medium">
                <span aria-hidden className="mt-0.5 text-muted transition-transform group-open:rotate-90">
                  ▸
                </span>
                <div className="min-w-0 flex-1">
                  <Markdown>{q.prompt_md}</Markdown>
                </div>
              </summary>
              {q.answer && (
                <div className="mt-3 flex flex-col gap-3 text-sm">
                  <div className="rounded-lg bg-bad-bg p-3">
                    <p className="font-semibold text-bad">Tu respuesta</p>
                    <Markdown>{optionText(q, q.answer.option_id)}</Markdown>
                  </div>
                  <div className="rounded-lg bg-good-bg p-3">
                    <p className="font-semibold text-good">Correcta</p>
                    <Markdown>{optionText(q, q.answer.correct_option_id)}</Markdown>
                  </div>
                  <Markdown>{q.answer.explanation_md}</Markdown>
                </div>
              )}
            </details>
          ))}
        </div>
      )}
    </section>
  );
}
