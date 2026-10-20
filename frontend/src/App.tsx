import { lazy, Suspense } from "react";

import { Loading } from "./components/Status";
import { parseHash, paths, useHash } from "./lib/router";
import { Home } from "./pages/Home";

// El juego (con Motion) y el historial se cargan al entrar: el inicio pesa lo mínimo.
const Play = lazy(() => import("./pages/Play"));
const History = lazy(() => import("./pages/History"));

export function App() {
  const route = parseHash(useHash());

  return (
    <div className="mx-auto flex min-h-dvh w-full max-w-2xl flex-col px-4 pb-10">
      <header className="flex items-center justify-between py-4">
        <a href={paths.home} className="flex min-h-11 items-center gap-2 font-semibold tracking-tight">
          <span
            aria-hidden
            className="grid size-7 place-items-center rounded-lg bg-accent text-sm font-bold text-accent-ink"
          >
            ?
          </span>
          Quiz de entrevistas
        </a>
        <a href={paths.history} className="flex min-h-11 items-center rounded-lg px-3 text-sm text-muted hover:text-ink">
          Historial
        </a>
      </header>
      <main className="flex flex-1 flex-col">
        <Suspense fallback={<Loading />}>
          {route.name === "home" && <Home />}
          {route.name === "history" && <History />}
          {route.name === "play" && <Play key={route.id} id={route.id} />}
          {route.name === "notfound" && (
            <p className="py-10 text-center text-muted">
              Esa página no existe. <a href={paths.home} className="text-accent underline">Ir al inicio</a>
            </p>
          )}
        </Suspense>
      </main>
    </div>
  );
}
