import type { Citation } from "./types";

export type StreamHandlers = {
  onRouter?: (d: { intent: string; job_seqs: number[] }) => void;
  onDelta: (text: string) => void;
  onCitations: (c: Citation[]) => void;
  onRefusal: () => void;
  onDone: (d: { message_id: string; meta: Record<string, unknown> }) => void;
  onError: (detail: string) => void;
};

export async function streamChat(
  message: string,
  h: StreamHandlers,
): Promise<void> {
  let resp: Response;
  try {
    resp = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
  } catch {
    h.onError("could not reach the server");
    return;
  }
  if (!resp.ok || !resp.body) {
    h.onError(`request failed (${resp.status})`);
    return;
  }

  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let idx: number;
    while ((idx = buffer.indexOf("\n\n")) !== -1) {
      const frame = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      let event = "message";
      let data = "";
      for (const line of frame.split("\n")) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        else if (line.startsWith("data:")) data += line.slice(5).trim();
      }
      if (!data) continue;
      let parsed: unknown;
      try {
        parsed = JSON.parse(data);
      } catch {
        continue;
      }
      switch (event) {
        case "router":
          h.onRouter?.(parsed as { intent: string; job_seqs: number[] });
          break;
        case "delta":
          h.onDelta((parsed as { text: string }).text);
          break;
        case "citations":
          h.onCitations(parsed as Citation[]);
          break;
        case "refusal":
          h.onRefusal();
          break;
        case "done":
          h.onDone(
            parsed as { message_id: string; meta: Record<string, unknown> },
          );
          break;
        case "error":
          h.onError((parsed as { detail: string }).detail);
          break;
      }
    }
  }
}
