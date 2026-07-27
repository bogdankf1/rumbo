"use client";

export function EmptyState({
  onLoadDemo,
  demoLoading,
}: {
  onLoadDemo: () => void;
  demoLoading: boolean;
}) {
  return (
    <div className="fade-up flex h-full flex-col items-center justify-center px-8 text-center">
      <h1 className="font-display text-4xl italic leading-tight">
        Where do you <span className="text-accent">actually</span> stand?
      </h1>
      <p className="mt-4 max-w-md text-sm leading-relaxed text-muted">
        Upload a resume and the roles you are eyeing. Rumbo reads both, scores
        every match deterministically, and answers your questions with the exact
        lines that back them up.
      </p>
      <button
        onClick={onLoadDemo}
        disabled={demoLoading}
        className="mt-8 rounded-full bg-accent px-6 py-2.5 text-sm font-medium text-bg transition hover:opacity-90 disabled:opacity-50"
      >
        {demoLoading ? "Setting the table..." : "Load demo data"}
      </button>
      <p className="mt-3 text-xs text-faint">
        or add your own documents in the sidebar
      </p>
    </div>
  );
}
