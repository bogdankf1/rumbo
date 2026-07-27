export default function Home() {
  return (
    <div className="flex h-screen flex-col">
      <header className="flex items-center justify-between border-b border-line px-6 py-3">
        <span className="font-display text-xl italic tracking-tight text-ink">
          Rumbo
        </span>
        <span className="text-sm text-muted">career intelligence</span>
      </header>
      <div className="flex min-h-0 flex-1">
        <aside className="w-80 shrink-0 border-r border-line bg-surface p-4">
          <p className="text-sm text-muted">Documents will live here.</p>
        </aside>
        <main className="flex flex-1 items-center justify-center">
          <p className="font-display text-2xl italic text-muted">
            Chat arrives in slice 3.
          </p>
        </main>
      </div>
    </div>
  );
}
