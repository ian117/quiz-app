import { api, unwrap } from "../api/client";
import { ErrorBox, Loading } from "../components/Status";
import { formatDate, MODE_LABEL, percent } from "../lib/format";
import { paths } from "../lib/router";
import { useResource } from "../lib/useResource";

const load = () => unwrap(api.GET("/sessions", { params: { query: { limit: 100 } } }));

export default function History() {
  const { data, error, loading, retry } = useResource(load);

  if (error) return <ErrorBox error={error} onRetry={retry} />;
  if (loading || !data) return <Loading />;

  return (
    <section className="flex flex-col gap-3">
      <h1 className="text-xl font-semibold">Historial</h1>
      {data.length === 0 && (
        <p className="py-8 text-center text-muted">
          Todavía no has jugado.{" "}
          <a href={paths.home} className="text-accent underline">
            Empieza una sesión
          </a>
        </p>
      )}
      <ul className="flex flex-col gap-2">
        {data.map((s) => {
          const done = s.finished_at !== null;
          return (
            <li key={s.id}>
              <a
                href={paths.play(s.id)}
                className="flex min-h-16 items-center justify-between gap-3 rounded-xl border border-line bg-surface px-4 py-3 hover:border-accent"
              >
                <span className="min-w-0">
                  <span className="block font-medium">{MODE_LABEL[s.mode]}</span>
                  <span className="block truncate text-sm text-muted">{formatDate(s.started_at)}</span>
                </span>
                <span className="shrink-0 text-right">
                  {done ? (
                    <>
                      <span className="block font-semibold tabular-nums">
                        {s.score}/{s.total}
                        <span className="ml-2 text-sm text-muted">{percent(s.score, s.total)}%</span>
                      </span>
                      <span className="block text-sm text-muted">Completa</span>
                    </>
                  ) : (
                    <>
                      <span className="block font-semibold text-accent">Continuar</span>
                      <span className="block text-sm text-muted tabular-nums">
                        {s.answered}/{s.total} respondidas
                      </span>
                    </>
                  )}
                </span>
              </a>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
