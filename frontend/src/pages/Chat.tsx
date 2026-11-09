import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api, ChatRequest, ChatSource, DEFAULT_LAT, DEFAULT_LON, ToolUse } from "../api";
import { DEFAULT_LATLON, LatLon, LatLonInput } from "../components/Inputs";
import { Markdown } from "../components/Markdown";

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
  const [failedRequest, setFailedRequest] = useState<ChatRequest | null>(null);
  const sending = useRef(false);
  const conversationRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const conversation = conversationRef.current;
    if (conversation) conversation.scrollTop = conversation.scrollHeight;
  }, [messages, loading]);

  function submit(request: ChatRequest, appendMessage: boolean) {
    if (sending.current) return;
    sending.current = true;
    if (appendMessage) setMessages(m => [...m, { role: "user", text: request.message }]);
    setLoading(true);
    setError(null);
    setFailedRequest(null);
    api.chat(request)
      .then(res => {
        setSessionId(res.session_id);
        setMessages(m => [...m, { role: "assistant", text: res.reply, toolUses: res.tool_uses, sources: res.sources }]);
      })
      .catch(reason => { setError(reason); setFailedRequest(request); })
      .finally(() => { sending.current = false; setLoading(false); });
  }

  function send() {
    const text = input.trim();
    if (!text || sending.current) return;
    setInput("");
    submit({
      message: text,
      session_id: sessionId,
      client_now: new Date().toISOString(),
      utc_offset: browserUtcOffset(),
      place: placeName(place),
      latitude: place.latitude,
      longitude: place.longitude,
    }, true);
  }

  function reset() {
    if (sending.current) return;
    if (sessionId) api.chatReset(sessionId).catch(() => {});
    setMessages([]);
    setSessionId(undefined);
    setInput("");
    setError(null);
    setFailedRequest(null);
  }

  return (
    <div className="chat-content" aria-busy={loading}>
      <p className="chat-intro">Ask about the book’s text, or ask it to compute something.</p>
      <details className="chat-place">
        <summary>
          Asking from {placeName(place)} ({place.latitude.toFixed(2)}, {place.longitude.toFixed(2)}),
          UTC{browserUtcOffset() >= 0 ? "+" : ""}{browserUtcOffset()}
        </summary>
        <LatLonInput value={place} onChange={setPlace} />
      </details>
      <div ref={conversationRef} className="chat-window" role="log" aria-label="Conversation" aria-live="polite">
        {messages.length === 0 && <p className="chat-empty">Ask a question while you explore. Your conversation stays here as you move between pages.</p>}
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
          <div className="chat-bubble" role="status">Thinking…</div>
        </div>}
      </div>
      {error != null && <div className="ss-error" role="alert">
        <p>{error instanceof Error ? error.message : String(error)}</p>
        {failedRequest && <button type="button" className="chat-retry" onClick={() => submit(failedRequest, false)} disabled={loading}>Retry</button>}
      </div>}
      <form className="chat-composer" noValidate onSubmit={event => { event.preventDefault(); send(); }}>
        <label className="project-sr-only" htmlFor="chat-message">Message</label>
        <textarea
          id="chat-message"
          rows={2}
          className="resize-none"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={event => {
            if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
              event.preventDefault();
              send();
            }
          }}
          placeholder="Ask about the Surya Siddhanta…"
        />
        <div className="chat-input-row">
          <button type="submit" disabled={loading || !input.trim()}>
            Send
          </button>
          <button type="button" onClick={reset} disabled={loading}>
            New chat
          </button>
        </div>
      </form>
    </div>
  );
}
