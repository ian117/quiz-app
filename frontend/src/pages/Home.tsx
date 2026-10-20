import { useState, type ReactNode } from "react";

import { api, unwrap, type Catalog } from "../api/client";
import { Chip, ErrorBox, Loading } from "../components/Status";
import {
  buildPlan,
  interviewPlan,
  MODES,
  ORDERS,
  phaseLabel,
  problemWith,
  type Setup,
} from "../lib/plan";
import { go, paths } from "../lib/router";
import { useResource } from "../lib/useResource";

const COUNTS = [5, 10, 20, null] as const;

const load = () => unwrap(api.GET("/catalog"));

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <fieldset className="flex flex-col gap-2">
      <legend className="mb-1 text-sm font-medium text-muted">{label}</legend>
      <div className="flex flex-wrap gap-2">{children}</div>
    </fieldset>
  );
}

function toggle(list: string[], item: string): string[] {
  return list.includes(item) ? list.filter((x) => x !== item) : [...list, item];
}

export function Home() {
  const { data: catalog, error, loading, retry } = useResource(load);

  if (error) return <ErrorBox error={error} onRetry={retry} />;
  if (loading || !catalog) return <Loading />;
  return <SetupForm catalog={catalog} />;
}

function SetupForm({ catalog }: { catalog: Catalog }) {
  const [setup, setSetup] = useState<Setup>({
    mode: "tema",
    topic: catalog.topics[0]?.slug ?? "",
    topics: [],
    area: "",
    tags: [],
    n: 10,
    order: "random",
  });
  const [starting, setStarting] = useState(false);
  const [startError, setStartError] = useState<Error | null>(null);

  const patch = (p: Partial<Setup>) => setSetup((s) => ({ ...s, ...p }));
  const problem = problemWith(setup, catalog);
  const fixedPlan = setup.mode === "entrevista";

  async function start() {
    setStarting(true);
    setStartError(null);
    try {
      const session = await unwrap(
        api.POST("/sessions", { body: { mode: setup.mode, plan: buildPlan(setup, catalog) } }),
      );
      go(paths.play(session.id));
    } catch (e) {
      setStartError(e as Error);
      setStarting(false);
    }
  }

  return (
    <form
      className="flex flex-col gap-6"
      onSubmit={(e) => {
        e.preventDefault();
        if (!problem && !starting) void start();
      }}
    >
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">¿Qué practicamos hoy?</h1>
        <p className="mt-1 text-muted">
          {catalog.topics.reduce((sum, t) => sum + t.question_count, 0)} preguntas en{" "}
          {catalog.topics.length} {catalog.topics.length === 1 ? "tema" : "temas"}.
        </p>
      </div>

      <Field label="Modo">
        {MODES.map((m) => (
          <Chip key={m.id} selected={setup.mode === m.id} onClick={() => patch({ mode: m.id })}>
            {m.label}
          </Chip>
        ))}
      </Field>
      <p className="-mt-3 text-sm text-muted">{MODES.find((m) => m.id === setup.mode)?.hint}</p>

      {setup.mode === "tema" && (
        <Field label="Tema">
          {catalog.topics.map((t) => (
            <Chip key={t.slug} selected={setup.topic === t.slug} onClick={() => patch({ topic: t.slug })}>
              {t.name} · {t.question_count}
            </Chip>
          ))}
        </Field>
      )}

      {setup.mode === "aleatoria" && (
        <Field label="Temas (elige dos o más)">
          {catalog.topics.map((t) => (
            <Chip
              key={t.slug}
              selected={setup.topics.includes(t.slug)}
              onClick={() => patch({ topics: toggle(setup.topics, t.slug) })}
            >
              {t.name} · {t.question_count}
            </Chip>
          ))}
        </Field>
      )}

      {setup.mode === "especializada" && (
        <>
          <Field label="Área">
            <Chip selected={setup.area === ""} onClick={() => patch({ area: "" })}>
              Cualquiera
            </Chip>
            {catalog.areas.map((a) => (
              <Chip key={a.slug} selected={setup.area === a.slug} onClick={() => patch({ area: a.slug })}>
                {a.slug} · {a.question_count}
              </Chip>
            ))}
          </Field>
          <Field label="Tags (basta con que tenga uno)">
            {catalog.tags.map((t) => (
              <Chip
                key={t.slug}
                selected={setup.tags.includes(t.slug)}
                onClick={() => patch({ tags: toggle(setup.tags, t.slug) })}
              >
                {t.slug} · {t.question_count}
              </Chip>
            ))}
          </Field>
        </>
      )}

      {fixedPlan && (
        <ol className="flex flex-col gap-1 rounded-xl border border-line bg-surface p-4 text-sm">
          {interviewPlan(catalog).map((phase, i) => (
            <li key={i}>
              <span className="mr-2 text-muted">Fase {i + 1}</span>
              {phaseLabel(phase)}
            </li>
          ))}
        </ol>
      )}

      {!fixedPlan && (
        <>
          <Field label="Cuántas">
            {COUNTS.map((n) => (
              <Chip key={n ?? "all"} selected={setup.n === n} onClick={() => patch({ n })}>
                {n ?? "Todas"}
              </Chip>
            ))}
          </Field>
          <Field label="Orden">
            {ORDERS.map((o) => (
              <Chip key={o.id} selected={setup.order === o.id} onClick={() => patch({ order: o.id })}>
                {o.label}
              </Chip>
            ))}
          </Field>
        </>
      )}

      {startError && <ErrorBox error={startError} />}

      <div className="sticky bottom-0 -mx-4 mt-2 bg-bg/90 px-4 py-3 backdrop-blur">
        {problem && (
          <p role="status" className="mb-2 text-center text-sm text-muted">
            {problem}
          </p>
        )}
        <button
          type="submit"
          disabled={problem !== null || starting}
          className="min-h-12 w-full rounded-xl bg-accent px-6 font-semibold text-accent-ink transition-opacity disabled:opacity-40"
        >
          {starting ? "Preparando…" : "Empezar"}
        </button>
      </div>
    </form>
  );
}
