"use client";

export function TopBar({
  onLoadDemo,
  demoLoading,
}: {
  onLoadDemo: () => void;
  demoLoading: boolean;
}) {
  return (
    <header className="flex items-center justify-between border-b border-line px-6 py-3">
      <div className="flex items-baseline gap-3">
        <span className="font-display text-2xl italic tracking-tight">Rumbo</span>
        <span className="text-xs uppercase tracking-[0.2em] text-faint">
          career intelligence
        </span>
      </div>
      <button
        onClick={onLoadDemo}
        disabled={demoLoading}
        className="rounded-full border border-accent/60 px-4 py-1.5 text-sm text-accent transition hover:bg-accent/10 disabled:opacity-50"
      >
        {demoLoading ? "Loading demo..." : "Load demo data"}
      </button>
    </header>
  );
}
