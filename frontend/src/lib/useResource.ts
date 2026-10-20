import { useEffect, useMemo, useState } from "react";

type State<T> = { token: object; data?: T; error?: Error };

/**
 * Carga datos al montar (o cuando cambia `load`, que debe ser estable) y permite reintentar.
 * `loading` es verdadero mientras el resultado guardado no sea de la carga actual.
 */
export function useResource<T>(load: () => Promise<T>) {
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState<State<T> | null>(null);
  const token = useMemo(() => ({ load, attempt }), [load, attempt]);

  useEffect(() => {
    let live = true;
    load().then(
      (data) => live && setState({ token, data }),
      (error: Error) => live && setState({ token, error }),
    );
    return () => {
      live = false;
    };
  }, [load, token]);

  const current = state?.token === token ? state : null;
  return {
    loading: current === null,
    data: current?.data,
    error: current?.error,
    retry: () => setAttempt((n) => n + 1),
  };
}
