"use client";

import { useEffect, useRef } from "react";
import type { UiMessage } from "./Chat";
import { MessageBubble } from "./MessageBubble";

export function MessageList({ messages }: { messages: UiMessage[] }) {
  const endRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto px-6 py-6">
      <div className="mx-auto max-w-2xl space-y-6">
        {messages.length === 0 && (
          <div className="fade-up pt-16 text-center">
            <p className="font-display text-2xl italic text-muted">
              Ask about your fit.
            </p>
            <p className="mt-2 text-sm text-faint">
              Every answer cites the exact lines it stands on.
            </p>
          </div>
        )}
        {messages.map((m) => (
          <MessageBubble key={m.id} message={m} />
        ))}
        <div ref={endRef} />
      </div>
    </div>
  );
}
