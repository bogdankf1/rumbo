"use client";

import { ThemeToggle } from "./ThemeToggle";

export function TopBar({
  onLoadDemo,
  demoLoading,
  hasDocs,
  onToggleSidebar,
}: {
  onLoadDemo: () => void;
  demoLoading: boolean;
  hasDocs: boolean;
  onToggleSidebar: () => void;
}) {
  return (
    <header className="flex items-center justify-between border-b border-line px-4 py-3 sm:px-6">
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleSidebar}
          aria-label="Toggle documents panel"
          className="flex h-7 w-7 items-center justify-center rounded-md border border-line text-muted transition hover:border-accent/60 hover:text-accent lg:hidden"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M3 6h18M3 12h18M3 18h18" />
          </svg>
        </button>
        <span className="font-display text-2xl italic tracking-tight">Rumbo</span>
        <span className="hidden text-xs uppercase tracking-[0.2em] text-faint sm:inline">
          career intelligence
        </span>
      </div>
      <div className="flex items-center gap-3">
        {hasDocs ? (
          <button
            onClick={onLoadDemo}
            disabled={demoLoading}
            className="text-xs text-faint transition hover:text-accent disabled:opacity-50"
          >
            {demoLoading ? "Resetting..." : "Reset demo data"}
          </button>
        ) : (
          <button
            onClick={onLoadDemo}
            disabled={demoLoading}
            className="rounded-full border border-accent/60 px-4 py-1.5 text-sm text-accent transition hover:bg-accent/10 disabled:opacity-50"
          >
            {demoLoading ? "Loading demo..." : "Load demo data"}
          </button>
        )}
        <ThemeToggle />
      </div>
    </header>
  );
}
