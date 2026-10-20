import { m } from "motion/react";
import { useEffect, useRef } from "react";

import type { QuestionOut } from "../api/client";
import { formatSeconds } from "../lib/format";
import { Markdown } from "./Markdown";
import { ErrorBox } from "./Status";

interface Props {
  question: QuestionOut;
  /** Posición (desde 1) y total, para anunciar la pregunta. */
  number: number;
  total: number;
  /** Fallo al enviar la respuesta. */
  error: Error | null;
  /** Opción enviada y todavía sin respuesta del servidor. */
  pending: number | null;
  isLast: boolean;
  onChoose: (optionId: number) => void;
  onNext: () => void;
}

export function QuestionCard({ question, number, total, error, pending, isLast, onChoose, onNext }: Props) {
  const { answer } = question;
  const headingRef = useRef<HTMLHeadingElement>(null);
  const feedbackRef = useRef<HTMLDivElement>(null);
  const nextRef = useRef<HTMLButtonElement>(null);

  // Al llegar una pregunta, el foco va a su encabezado: se anuncia y Tab sigue desde ahí.
  useEffect(() => {
    headingRef.current?.focus({ preventScroll: true });
  }, []);

  // Con el foco en «Seguir», Enter hace lo esperado sin handlers extra. Antes se muestra el
  // feedback entero (o su inicio, si es más alto que la pantalla).
  const answered = answer !== null;
  useEffect(() => {
    if (!answered) return;
    const feedback = feedbackRef.current;
    if (feedback) {
      const tall = feedback.getBoundingClientRect().height > window.innerHeight * 0.7;
      feedback.scrollIntoView({ block: tall ? "start" : "nearest" });
    }
    nextRef.current?.focus({ preventScroll: true });
  }, [answered]);

  return (
    <m.article
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.18 }}
      className="flex flex-col gap-4"
    >
      <h2 ref={headingRef} tabIndex={-1} className="sr-only">
        Pregunta {number} de {total}
      </h2>
      <div className="flex flex-wrap gap-1.5">
        <span className="rounded-full bg-surface2 px-2.5 py-0.5 text-xs text-muted">{question.topic}</span>
        {question.tags.map((tag) => (
          <span key={tag} className="rounded-full bg-surface2 px-2.5 py-0.5 text-xs text-muted">
            {tag}
          </span>
        ))}
      </div>

      <div className="rounded-2xl border border-line bg-surface p-4 text-lg">
        <Markdown>{question.prompt_md}</Markdown>
      </div>

      <ul className="flex flex-col gap-2.5">
        {question.options.map((option, i) => {
          const isChosen = answer?.option_id === option.id;
          const isCorrect = answer?.correct_option_id === option.id;
          const state = !answer
            ? pending === option.id
              ? "border-accent bg-surface"
              : "border-edge bg-surface hover:border-accent"
            : isCorrect
              ? "border-good bg-good-bg"
              : isChosen
                ? "border-bad bg-bad-bg"
                : "border-line bg-surface text-muted";
          return (
            <li key={option.id}>
              <button
                type="button"
                disabled={answered || pending !== null}
                onClick={() => onChoose(option.id)}
                className={`flex min-h-14 w-full items-start gap-3 rounded-xl border-2 px-3.5 py-3 text-left transition-colors ${state}`}
              >
                <kbd
                  aria-hidden
                  className="mt-0.5 grid size-6 shrink-0 place-items-center rounded-md bg-surface2 font-mono text-xs text-muted"
                >
                  {i + 1}
                </kbd>
                <span className="min-w-0 flex-1">
                  <Markdown>{option.text_md}</Markdown>
                </span>
                {answered && isCorrect && <span className="sr-only">Correcta</span>}
                {answered && isChosen && !isCorrect && <span className="sr-only">Tu respuesta, incorrecta</span>}
                {answered && (isCorrect || isChosen) && (
                  <span aria-hidden className={`font-bold ${isCorrect ? "text-good" : "text-bad"}`}>
                    {isCorrect ? "✓" : "✗"}
                  </span>
                )}
              </button>
            </li>
          );
        })}
      </ul>

      {error && <ErrorBox title="No se guardó tu respuesta" error={error} hint="Elige otra vez para reintentar." />}

      <div ref={feedbackRef} role="status" aria-live="polite">
        {answer && (
          <m.section
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.18 }}
            className={`rounded-2xl border p-4 ${
              answer.is_correct ? "border-good bg-good-bg" : "border-bad bg-bad-bg"
            }`}
          >
            <p className={`font-semibold ${answer.is_correct ? "text-good" : "text-bad"}`}>
              {answer.is_correct ? "¡Correcto!" : "Incorrecto"}
              <span className="ml-2 text-sm font-normal text-muted">{formatSeconds(answer.time_ms)}</span>
            </p>
            <div className="mt-2">
              <Markdown>{answer.explanation_md}</Markdown>
            </div>
          </m.section>
        )}
      </div>

      {answer && (
        <button
          ref={nextRef}
          type="button"
          onClick={onNext}
          className="min-h-12 rounded-xl bg-accent px-6 font-semibold text-accent-ink"
        >
          {isLast ? "Ver resultado" : "Seguir"} <span aria-hidden>↵</span>
        </button>
      )}
    </m.article>
  );
}
