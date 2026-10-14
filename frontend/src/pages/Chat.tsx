import { useState } from "react";
import { api } from "../api";
import { PageHeader } from "../components/Tables";

interface ToolUse {
  tool: string;
  input: Record<string, unknown>;
  result: string;
}

interface Message {
  role: "user" | "assistant";
  text: string;
  toolUses?: ToolUse[];
}

export function Chat() {
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);

  function send() {
    const text = input.trim();
    if (!text || loading) return;
    setMessages((m) => [...m, { role: "user", text }]);
    setInput("");
    setLoading(true);
    api
      .chat({ message: text, session_id: sessionId })
      .then((r) => {
        const res = r as { session_id: string; reply: string; tool_uses: ToolUse[] };
        setSessionId(res.session_id);
        setMessages((m) => [...m, { role: "assistant", text: res.reply, toolUses: res.tool_uses }]);
        setError(null);
      })
      .catch(setError)
      .finally(() => setLoading(false));
  }

  function reset() {
    if (sessionId) api.chatReset(sessionId).catch(() => {});
    setMessages([]);
  }

  return (
    <div className="chat-page">
      <PageHeader title="Surya Siddhanta AI" subtitle="Ask about the book's text, or ask it to compute something" />
      <div className="chat-window">
        {messages.map((m, i) => (
          <div key={i} className={`chat-msg chat-${m.role}`}>
            <div className="chat-bubble">{m.text}</div>
            {m.toolUses && m.toolUses.length > 0 && (
              <details className="tool-trace">
                <summary>{m.toolUses.length} tool call(s)</summary>
                {m.toolUses.map((tu, j) => (
                  <div key={j} className="tool-trace-item">
                    <strong>{tu.tool}</strong>({JSON.stringify(tu.input)})
                    <pre>{tu.result}</pre>
                  </div>
                ))}
              </details>
            )}
          </div>
        ))}
        {loading && <div className="chat-msg chat-assistant">
          <div className="chat-bubble">…</div>
        </div>}
      </div>
      {error != null && <div className="ss-error">Error: {error instanceof Error ? error.message : String(error)}</div>}
      <div className="chat-input-row">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder="Ask about the Surya Siddhanta…"
        />
        <button onClick={send} disabled={loading}>
          Send
        </button>
        <button onClick={reset} disabled={loading}>
          Reset
        </button>
      </div>
    </div>
  );
}
