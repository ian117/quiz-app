import { lazy, Suspense } from "react";

// react-markdown y el resaltado salen del JS inicial: llegan después, mientras se ve el texto plano.
const MarkdownImpl = lazy(() => import("./MarkdownImpl"));

export function Markdown({ children }: { children: string }) {
  return (
    <Suspense fallback={<p className="whitespace-pre-wrap leading-relaxed">{children}</p>}>
      <MarkdownImpl>{children}</MarkdownImpl>
    </Suspense>
  );
}
