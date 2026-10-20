import { LazyMotion, m, MotionConfig } from "motion/react";
import { useCallback, useEffect, useEffectEvent, useRef, useState } from "react";

import { api, ApiError, unwrap, type SessionOut } from "../api/client";
import { QuestionCard } from "../components/QuestionCard";
import { Results } from "../components/Results";
import { ErrorBox, Loading } from "../components/Status";
import { firstUnanswered, optionIndexForKey, streaks } from "../lib/game";
import { paths } from "../lib/router";
import { useResource } from "../lib/useResource";

// Las funciones de Motion llegan después del primer pintado.
const loadFeatures = () => import("../lib/motionFeatures").then((mod) => mod.default);

export default function Play({ id }: { id: number }) {
  const load = useCallback(
    () => unwrap(api.GET("/sessions/{session_id}", { params: { path: { session_id: id } } })),
    [id],
  );
  const { data, error, loading, retry } = useResource(load);

  if (error) {
    return (
      <>
        <ErrorBox error={error} onRetry={error instanceof ApiError && error.status === 404 ? undefined : retry} />
        <a href={paths.home} className="text-center text-accent underline">
          Volver al inicio
        </a>
      </>
    );
  }
  if (loading || !data) return <Loading />;

  return (
    <MotionConfig reducedMotion="user">
      <LazyMotion features={loadFeatures} strict>
        <Game initial={data} />
      </LazyMotion>
    </MotionConfig>
  );
}

function Game({ initial }: { initial: SessionOut }) {
  const [session, setSession] = useState(initial);
  const [index, setIndex] = useState(() => firstUnanswered(initial.questions));
  const [pending, setPending] = useState<number | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const shownAt = useRef(0);

  const question = session.questions[index];
  const { current: streak } = streaks(session.questions);

  useEffect(() => {
    shownAt.current = performance.now();
  }, [index]);

  async function choose(optionId: number) {
    if (!question || question.answer || pending !== null) return;
    setPending(optionId);
    setError(null);
    try {
      const result = await unwrap(
        api.POST("/sessions/{session_id}/answers", {
          params: { path: { session_id: session.id } },
          body: {
            question_id: question.id,
            option_id: optionId,
            time_ms: Math.round(performance.now() - shownAt.current),
          },
        }),
      );
      setSession((s) => ({
        ...s,
        score: result.score,
        answered: result.answered,
        finished_at: result.finished ? new Date().toISOString() : s.finished_at,
        questions: s.questions.map((q) => (q.id === result.answer.question_id ? { ...q, answer: result.answer } : q)),
      }));
    } catch (e) {
      let failure = e as Error;
      if (e instanceof ApiError && e.status === 409) {
        // Ya estaba respondida (otra pestaña): se muestra lo que dice el servidor.
        try {
          setSession(await unwrap(api.GET("/sessions/{session_id}", { params: { path: { session_id: session.id } } })));
          return;
        } catch (reloadError) {
          failure = reloadError as Error;
        }
      }
      setError(failure);
    } finally {
      setPending(null);
    }
  }

  function next() {
    setIndex((i) => i + 1);
  }

  const onKey = useEffectEvent((e: KeyboardEvent) => {
    if (e.repeat || e.metaKey || e.ctrlKey || e.altKey || !question) return;
    const target = e.target;
    if (target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement) return;
    if (!question.answer) {
      const i = optionIndexForKey(e.key, question.options.length);
      const option = i === null ? undefined : question.options[i];
      if (option) {
        e.preventDefault();
        void choose(option.id);
      }
    } else if (e.key === "Enter" && !(target instanceof HTMLButtonElement || target instanceof HTMLAnchorElement)) {
      e.preventDefault();
      next();
    }
  });

  useEffect(() => {
    const listener = (e: KeyboardEvent) => onKey(e);
    window.addEventListener("keydown", listener);
    return () => window.removeEventListener("keydown", listener);
  }, []);

  if (!question) return <Results session={session} />;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-3">
        <div
          role="progressbar"
          aria-valuemin={0}
          aria-valuemax={session.total}
          aria-valuenow={session.answered}
          aria-label="Progreso"
          className="h-2 flex-1 overflow-hidden rounded-full bg-surface2"
        >
          <m.div
            className="h-full origin-left rounded-full bg-accent"
            initial={false}
            animate={{ scaleX: session.answered / session.total }}
            transition={{ duration: 0.25 }}
          />
        </div>
        <span className="text-sm tabular-nums text-muted">
          {index + 1}/{session.total}
        </span>
        <span className="min-w-12 text-right text-sm font-semibold tabular-nums">
          {streak > 1 && (
            <m.span
              key={streak}
              className="inline-block"
              initial={{ scale: 1.5 }}
              animate={{ scale: 1 }}
              transition={{ type: "spring", stiffness: 500, damping: 15 }}
            >
              <span className="sr-only">Racha de </span>
              <span aria-hidden>🔥 </span>
              {streak}
            </m.span>
          )}
        </span>
      </div>

      <QuestionCard
        key={question.id}
        question={question}
        number={index + 1}
        total={session.total}
        error={error}
        pending={pending}
        isLast={index === session.questions.length - 1}
        onChoose={(optionId) => void choose(optionId)}
        onNext={next}
      />
    </div>
  );
}
