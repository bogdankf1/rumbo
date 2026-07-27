"use client";

import { useState } from "react";
import type { Citation } from "@/lib/types";
import type { UiMessage } from "./Chat";

function ContentWithCitations({
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
  const parts = content.split(/(\[E\d+\])/g);

  return (
    <>
      {parts.map((part, i) => {
        const marker = part.match(/^\[(E\d+)\]$/);
        if (!marker) return <span key={i}>{part}</span>;
        const citation = byId.get(marker[1]);
        if (!citation) return null;
        return (
          <button
            key={i}
            onClick={() => onOpen(citation)}
            className="mx-0.5 inline-flex h-4 min-w-4 -translate-y-1 items-center justify-center rounded-full bg-accent/20 px-1 font-mono text-[10px] text-accent transition hover:bg-accent/40"
            aria-label={`Show source ${numbers.get(citation.id)}`}
          >
            {numbers.get(citation.id)}
          </button>
        );
      })}
    </>
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
        className={`whitespace-pre-wrap text-[15px] leading-relaxed ${
          message.streaming ? "stream-caret" : ""
        }`}
      >
        <ContentWithCitations
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
