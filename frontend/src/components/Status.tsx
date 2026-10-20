import type { ReactNode } from "react";

export function Loading() {
  return (
    <div role="status" aria-label="Cargando" className="flex flex-col gap-3 py-6 motion-reduce:*:animate-none">
      <div className="h-6 w-2/3 animate-pulse rounded-lg bg-surface2" />
      <div className="h-24 animate-pulse rounded-2xl bg-surface2" />
      <div className="h-14 animate-pulse rounded-xl bg-surface2" />
      <div className="h-14 animate-pulse rounded-xl bg-surface2" />
    </div>
  );
}

export function ErrorBox({
  error,
  onRetry,
  title = "Algo salió mal",
  hint,
}: {
  error: Error;
  onRetry?: () => void;
  title?: string;
  hint?: string;
}) {
  return (
    <div role="alert" className="my-6 rounded-2xl border border-line bg-bad-bg p-4 text-bad">
      <p className="font-medium">{title}</p>
      <p className="mt-1 text-sm">
        {error.message}
        {hint && ` ${hint}`}
      </p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-3 rounded-lg bg-surface px-3 py-2 text-sm font-medium text-ink"
        >
          Reintentar
        </button>
      )}
    </div>
  );
}

export function Chip({
  children,
  selected,
  onClick,
  disabled,
}: {
  children: ReactNode;
  selected?: boolean;
  onClick?: () => void;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      aria-pressed={selected}
      onClick={onClick}
      className={`min-h-11 min-w-11 rounded-full border px-4 text-sm transition-colors disabled:opacity-40 ${
        selected
          ? "border-accent bg-accent text-accent-ink"
          : "border-edge bg-surface text-ink hover:border-accent"
      }`}
    >
      {children}
    </button>
  );
}
