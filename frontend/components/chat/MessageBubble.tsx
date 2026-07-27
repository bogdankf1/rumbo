"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import type { Citation } from "@/lib/types";
import type { UiMessage } from "./Chat";

function AssistantMarkdown({
  content,
  citations,
  onOpen,
}: {
  content: string;
  citations: Citation[];
  onOpen: (c: Citation) => void;
}) {
  const byId = new Map(citations.map((c) => [c.id, c] as const));
  const numbers = new Map(citations.map((c, i) => [c.id, i + 1] as const));
  // Citation markers become links so the markdown renderer carries them
  // through paragraphs and bullets; the link component renders the chip.
  const md = content.replace(/\[(E\d+)\]/g, (_m, id) => `[${id}](#cite-${id})`);

  return (
    <ReactMarkdown
      components={{
        a: ({ href, children }) => {
          const id = href?.startsWith("#cite-")
            ? href.slice("#cite-".length)
            : null;
          const citation = id ? byId.get(id) : undefined;
          if (!citation) return null; // marker still streaming in, or a stray link
          return (
            <button
              onClick={() => onOpen(citation)}
              aria-label={`Show source ${numbers.get(citation.id)}`}
              className="mx-0.5 inline-flex h-4 min-w-4 -translate-y-1 items-center justify-center rounded-full bg-accent/20 px-1 font-mono text-[10px] not-italic text-accent transition hover:bg-accent/40"
            >
              {numbers.get(citation.id)}
            </button>
          );
        },
        p: ({ children }) => <p className="mb-2.5 last:mb-0">{children}</p>,
        ul: ({ children }) => (
          <ul className="mb-2.5 space-y-1.5 last:mb-0">{children}</ul>
        ),
        ol: ({ children }) => (
          <ol className="mb-2.5 list-decimal space-y-1.5 pl-5 last:mb-0">
            {children}
          </ol>
        ),
        li: ({ children }) => (
          <li className="relative pl-4 before:absolute before:left-0 before:text-faint before:content-['-']">
            {children}
          </li>
        ),
        strong: ({ children }) => (
          <strong className="font-semibold text-ink">{children}</strong>
        ),
        em: ({ children }) => <em className="italic">{children}</em>,
      }}
    >
      {md}
    </ReactMarkdown>
  );
}

export function MessageBubble({ message }: { message: UiMessage }) {
  const [open, setOpen] = useState<Citation | null>(null);

  if (message.role === "user") {
    return (
      <div className="fade-up flex justify-end">
        <p className="max-w-[85%] rounded-2xl rounded-br-sm bg-raised px-4 py-2.5 font-display text-[15px] italic leading-relaxed">
          {message.content}
        </p>
      </div>
    );
  }

  return (
    <div className="fade-up">
      {message.refused && (
        <span className="mb-1.5 inline-block rounded-full border border-line px-2 py-0.5 text-[10px] uppercase tracking-widest text-faint">
          outside my scope
        </span>
      )}
      <div
        className={`text-[15px] leading-relaxed ${
          message.streaming ? "stream-caret" : ""
        }`}
      >
        <AssistantMarkdown
          content={message.content}
          citations={message.citations}
          onOpen={(c) => setOpen((prev) => (prev?.id === c.id ? null : c))}
        />
      </div>
      {open && (
        <div className="fade-up mt-3 rounded-lg border border-line bg-surface p-3 text-sm">
          <p className="text-[10px] uppercase tracking-widest text-accent">
            {open.doc_label}
          </p>
          <p className="mt-1.5 italic leading-relaxed text-muted">
            &ldquo;{open.quote}&rdquo;
          </p>
        </div>
      )}
    </div>
  );
}
