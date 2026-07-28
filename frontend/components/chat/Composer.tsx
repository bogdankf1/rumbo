"use client";

import { useState } from "react";

const SUGGESTIONS = [
  "What skills am I missing for Job #2?",
  "Which of these roles fits me best and why?",
  "Help me prep for the Job #5 interview",
];

export function Composer({
  onSend,
  busy,
  empty,
}: {
  onSend: (t: string) => void;
  busy: boolean;
  empty: boolean;
}) {
  const [text, setText] = useState("");

  function submit() {
    const t = text.trim();
    if (!t || busy) return;
    setText("");
    onSend(t);
  }

  return (
    <div className="border-t border-line px-4 py-4 sm:px-6">
      <div className="mx-auto max-w-2xl">
        {empty && (
          <div className="mb-3 flex flex-wrap justify-center gap-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => !busy && onSend(s)}
                className="rounded-full border border-line px-3 py-1.5 text-xs text-muted transition hover:border-accent/60 hover:text-accent"
              >
                {s}
              </button>
            ))}
          </div>
        )}
        <div className="flex items-end gap-3 rounded-xl border border-line bg-surface px-4 py-3 transition focus-within:border-accent/50">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                submit();
              }
            }}
            placeholder={
              busy ? "Thinking..." : "Ask about fit, gaps, or interview prep"
            }
            rows={1}
            className="max-h-40 flex-1 resize-none bg-transparent text-[15px] outline-none placeholder:text-faint"
          />
          <button
            onClick={submit}
            disabled={busy || !text.trim()}
            className="rounded-full bg-accent px-4 py-1.5 text-sm font-medium text-bg transition hover:opacity-90 disabled:opacity-40"
          >
            Ask
          </button>
        </div>
      </div>
    </div>
  );
}
