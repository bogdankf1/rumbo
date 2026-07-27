"use client";

import { useState } from "react";

export function PasteJobModal({
  onSubmit,
  onClose,
}: {
  onSubmit: (title: string | null, text: string) => Promise<void>;
  onClose: () => void;
}) {
  const [title, setTitle] = useState("");
  const [text, setText] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    if (!text.trim() || pending) return;
    setError(null);
    setPending(true);
    try {
      await onSubmit(title.trim() || null, text);
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : "could not add the position");
      setPending(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-6"
      onClick={onClose}
    >
      <div
        className="fade-up w-full max-w-xl rounded-xl border border-line bg-surface p-5"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="font-display text-lg italic">Paste a job description</h2>
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Title (optional, extracted from the text if left blank)"
          className="mt-4 w-full rounded-lg border border-line bg-raised px-3 py-2 text-sm outline-none placeholder:text-faint focus:border-accent/60"
        />
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Paste the full posting text here"
          rows={10}
          className="mt-3 w-full resize-none rounded-lg border border-line bg-raised px-3 py-2 text-sm outline-none placeholder:text-faint focus:border-accent/60"
        />
        {error && <p className="mt-2 text-xs text-weak">{error}</p>}
        <div className="mt-4 flex justify-end gap-3">
          <button onClick={onClose} className="text-sm text-muted hover:text-ink">
            Cancel
          </button>
          <button
            onClick={submit}
            disabled={pending || !text.trim()}
            className="rounded-full bg-accent px-4 py-1.5 text-sm text-bg transition hover:opacity-90 disabled:opacity-50"
          >
            {pending ? "Reading the posting..." : "Add position"}
          </button>
        </div>
      </div>
    </div>
  );
}
