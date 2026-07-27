"use client";

import { useCallback, useEffect, useState } from "react";
import { listMessages } from "@/lib/api";
import { streamChat } from "@/lib/sse";
import type { Citation } from "@/lib/types";
import { Composer } from "./Composer";
import { MessageList } from "./MessageList";

export type UiMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: Citation[];
  refused: boolean;
  streaming?: boolean;
};

export function Chat() {
  const [messages, setMessages] = useState<UiMessage[]>([]);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    listMessages()
      .then((rows) =>
        setMessages(
          rows.map((m) => ({
            id: m.id,
            role: m.role,
            content: m.content,
            citations: m.citations ?? [],
            refused: m.role === "assistant" && m.intent === "out_of_scope",
          })),
        ),
      )
      .catch(() => {});
  }, []);

  const send = useCallback(
    async (text: string) => {
      if (busy) return;
      setBusy(true);
      const draftId = `draft-${Date.now()}`;
      setMessages((prev) => [
        ...prev,
        {
          id: `user-${Date.now()}`,
          role: "user",
          content: text,
          citations: [],
          refused: false,
        },
        {
          id: draftId,
          role: "assistant",
          content: "",
          citations: [],
          refused: false,
          streaming: true,
        },
      ]);
      const patch = (fn: (m: UiMessage) => UiMessage) =>
        setMessages((prev) => prev.map((m) => (m.id === draftId ? fn(m) : m)));

      await streamChat(text, {
        onDelta: (t) => patch((m) => ({ ...m, content: m.content + t })),
        onCitations: (c) => patch((m) => ({ ...m, citations: c })),
        onRefusal: () => patch((m) => ({ ...m, refused: true })),
        onDone: (d) =>
          patch((m) => ({ ...m, id: d.message_id, streaming: false })),
        onError: (detail) =>
          patch((m) => ({
            ...m,
            streaming: false,
            content: m.content || `Something went wrong: ${detail}`,
          })),
      });
      setBusy(false);
    },
    [busy],
  );

  return (
    <div className="flex h-full flex-col">
      <MessageList messages={messages} />
      <Composer onSend={send} busy={busy} empty={messages.length === 0} />
    </div>
  );
}
