"use client";

import { useRef, useState } from "react";

export function UploadZone({
  label,
  pendingLabel,
  onFile,
  compact = false,
}: {
  label: string;
  pendingLabel: string;
  onFile: (file: File) => Promise<void>;
  compact?: boolean;
}) {
  const input = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handle(file: File | undefined) {
    if (!file || pending) return;
    setError(null);
    setPending(true);
    try {
      await onFile(file);
    } catch (e) {
      setError(e instanceof Error ? e.message : "upload failed");
    } finally {
      setPending(false);
    }
  }

  return (
    <div>
      <div
        onClick={() => input.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          handle(e.dataTransfer.files[0]);
        }}
        className={`cursor-pointer rounded-lg border border-dashed text-center transition ${
          compact ? "px-3 py-2 text-xs" : "px-4 py-5 text-sm"
        } ${
          dragging
            ? "border-accent bg-accent/10 text-accent"
            : "border-line text-faint hover:border-faint hover:text-muted"
        }`}
      >
        {pending ? (
          <span className="text-accent">{pendingLabel}</span>
        ) : (
          label
        )}
      </div>
      {error && <p className="mt-1 text-xs text-weak">{error}</p>}
      <input
        ref={input}
        type="file"
        accept="application/pdf"
        className="hidden"
        onChange={(e) => {
          handle(e.target.files?.[0]);
          e.target.value = "";
        }}
      />
    </div>
  );
}
