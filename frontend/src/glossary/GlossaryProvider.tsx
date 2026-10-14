import { createContext, ReactNode, useCallback, useContext, useEffect, useState } from "react";
import { api } from "../api";
import { buildIndex, TermIndex } from "./matchTerms";

/** Load state of the glossary document. */
export type GlossaryStatus = "loading" | "ready" | "error";

/** What the glossary context hands to the panel and its hooks. */
export interface GlossaryState {
  status: GlossaryStatus;
  index: TermIndex | null;
  /** Fetch the document again after an error. */
  retry: () => void;
}

const GlossaryContext = createContext<GlossaryState>({
  status: "loading",
  index: null,
  retry: () => {},
});

/**
 * Fetches the glossary once for the whole app and builds its scan index.
 *
 * The fetch never blocks a page: pages render immediately and the panel
 * fills in when the document arrives. The browser's HTTP cache revalidates
 * with the server's ETag, so later visits cost a 304.
 */
export function GlossaryProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<GlossaryStatus>("loading");
  const [index, setIndex] = useState<TermIndex | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setStatus("loading");
    api
      .glossary()
      .then((doc) => {
        if (cancelled) return;
        setIndex(buildIndex(doc));
        setStatus("ready");
      })
      .catch(() => {
        if (!cancelled) setStatus("error");
      });
    return () => {
      cancelled = true;
    };
  }, [attempt]);

  const retry = useCallback(() => setAttempt((n) => n + 1), []);

  return (
    <GlossaryContext.Provider value={{ status, index, retry }}>{children}</GlossaryContext.Provider>
  );
}

/** The glossary's load state and index. */
export function useGlossary(): GlossaryState {
  return useContext(GlossaryContext);
}
