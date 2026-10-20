import { useEffect, useState } from "react";
import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";

function CodeBlock({ code, lang }: { code: string; lang: string }) {
  const [html, setHtml] = useState<string | null>(null);

  useEffect(() => {
    let live = true;
    void import("../lib/highlight").then(({ highlight }) => {
      if (live) setHtml(highlight(code, lang));
    });
    return () => {
      live = false;
    };
  }, [code, lang]);

  return (
    <pre>
      {html === null ? (
        <code>{code}</code>
      ) : (
        // highlight.js escapa el HTML que devuelve.
        <code className="hljs" dangerouslySetInnerHTML={{ __html: html }} />
      )}
    </pre>
  );
}

const components: Components = {
  // CodeBlock pinta su propio <pre>.
  pre: ({ children }) => <>{children}</>,
  code({ className, children }) {
    const text = String(children).replace(/\n$/, "");
    const lang = /language-(\w+)/.exec(className ?? "")?.[1];
    if (lang !== undefined || text.includes("\n")) return <CodeBlock code={text} lang={lang ?? ""} />;
    return <code>{children}</code>;
  },
  a: ({ href, children }) => (
    <a href={href} target="_blank" rel="noreferrer noopener">
      {children}
    </a>
  ),
};

export default function MarkdownImpl({ children }: { children: string }) {
  return (
    <div className="md">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {children}
      </ReactMarkdown>
    </div>
  );
}
