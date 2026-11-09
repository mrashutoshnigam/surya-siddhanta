import { useState } from "react";
import { Link } from "react-router-dom";
import { api, ChatSource, DEFAULT_LAT, DEFAULT_LON, ToolUse } from "../api";
import { DEFAULT_LATLON, LatLon, LatLonInput } from "../components/Inputs";
import { Markdown } from "../components/Markdown";
import { PageHeader } from "../components/Tables";

interface Message {
  role: "user" | "assistant";
  text: string;
  toolUses?: ToolUse[];
  sources?: ChatSource[];
}

/** The browser's offset from UTC in hours (IST gives 5.5). */
function browserUtcOffset(): number {
  return -new Date().getTimezoneOffset() / 60;
}

/** Label for the place the chat sends: Ujjain at the defaults, else coordinates. */
function placeName(p: LatLon): string {
  return p.latitude === DEFAULT_LAT && p.longitude === DEFAULT_LON ? "Ujjain" : "the given coordinates";
}

/** Citation chips for one answer: verses link to their chapter page, commentary shows its page. */
function Sources({ sources }: { sources: ChatSource[] }) {
  return (
    <div className="chat-sources">
      <span className="chat-sources-label">Sources:</span>
      {sources.map((s) =>
        s.kind === "verse" && s.chapter ? (
          <Link key={s.id} className="chat-source" to={`/book/${s.chapter}`} title={s.snippet}>
            {s.label}
          </Link>
        ) : (
          <span key={s.id} className="chat-source chat-source-commentary" title={s.snippet}>
            {s.label}
          </span>
        ),
      )}
    </div>
  );
}

export function Chat() {
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [place, setPlace] = useState<LatLon>(DEFAULT_LATLON);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);

  function send() {
    const text = input.trim();
    if (!text || loading) return;
    setMessages((m) => [...m, { role: "user", text }]);
    setInput("");
    setLoading(true);
    api
      .chat({
        message: text,
        session_id: sessionId,
        client_now: new Date().toISOString(),
        utc_offset: browserUtcOffset(),
        place: placeName(place),
        latitude: place.latitude,
        longitude: place.longitude,
      })
      .then((res) => {
        setSessionId(res.session_id);
        setMessages((m) => [
          ...m,
          { role: "assistant", text: res.reply, toolUses: res.tool_uses, sources: res.sources },
        ]);
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
      <details className="chat-place">
        <summary>
          Asking from {placeName(place)} ({place.latitude.toFixed(2)}, {place.longitude.toFixed(2)}),
          UTC{browserUtcOffset() >= 0 ? "+" : ""}{browserUtcOffset()}
        </summary>
        <LatLonInput value={place} onChange={setPlace} />
      </details>
      <div className="chat-window">
        {messages.map((m, i) => (
          <div key={i} className={`chat-msg chat-${m.role}`}>
            <div className="chat-bubble">
              {m.role === "assistant" ? <Markdown>{m.text}</Markdown> : m.text}
            </div>
            {m.sources && m.sources.length > 0 && <Sources sources={m.sources} />}
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
