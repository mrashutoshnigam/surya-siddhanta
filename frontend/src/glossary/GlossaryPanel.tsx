import { lazy, Suspense, useEffect, useMemo, useState } from "react";
import { useGlossary } from "./GlossaryProvider";
import { CATEGORY_LABELS, CATEGORY_ORDER, Category, TermEntry } from "./types";
import { useTermsOnPage } from "./useTermsOnPage";

/**
 * The popup and KaTeX (its code, CSS and fonts) load together, on the first
 * term a reader opens, so no page pays for them up front.
 */
const TermDialog = lazy(() => import("./TermDialog").then((m) => ({ default: m.TermDialog })));

/** True when a term's name, aliases or short definition contain `query`. */
function termMatchesFilter(term: TermEntry, query: string): boolean {
  if (!query) return true;
  const haystack = [term.term, term.short, ...(term.aliases ?? [])].join("\n").toLowerCase();
  return haystack.includes(query);
}

/** Terms grouped by category, in panel order, empty groups dropped. */
function groupByCategory(terms: TermEntry[]): { category: Category; terms: TermEntry[] }[] {
  return CATEGORY_ORDER.map((category) => ({
    category,
    terms: terms.filter((t) => t.category === category),
  })).filter((g) => g.terms.length > 0);
}

/** One clickable row: bold name over the one-line definition. */
function TermRow({ term, onOpen }: { term: TermEntry; onOpen: (id: string) => void }) {
  return (
    <li>
      <button type="button" className="term-row" onClick={() => onOpen(term.id)}>
        <span className="term-row-name">{term.term}</span>
        <span className="term-row-short">{term.short}</span>
      </button>
    </li>
  );
}

/** Persistent glossary content inside the shared Terms tab. */
export function GlossaryPanel({ active }: { active: boolean }) {
  const { status, index, retry } = useGlossary();
  const { core, found } = useTermsOnPage();
  const [filter, setFilter] = useState("");
  const [dialogId, setDialogId] = useState<string | null>(null);
  useEffect(() => {
    if (!active) setDialogId(null);
  }, [active]);

  const query = filter.trim().toLowerCase();
  const coreShown = useMemo(() => core.filter((t) => termMatchesFilter(t, query)), [core, query]);
  const foundGroups = useMemo(
    () => groupByCategory(found.filter((t) => termMatchesFilter(t, query))),
    [found, query],
  );
  const total = core.length + found.length;
  const shown = coreShown.length + foundGroups.reduce((n, g) => n + g.terms.length, 0);

  const dialog = active && dialogId && index && (
    <Suspense fallback={null}>
      <TermDialog id={dialogId} index={index} onClose={() => setDialogId(null)} />
    </Suspense>
  );

  return (
      <div className="glossary-content">
        <header className="glossary-head">
          <h2>
            Terms on this page <span className="glossary-count">{total}</span>
          </h2>
        </header>
        <input
          type="search"
          className="glossary-filter"
          placeholder="Filter terms"
          aria-label="Filter terms"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        />
        <div className="glossary-body">
          {status === "loading" && <p className="glossary-note">Loading definitions…</p>}
          {status === "error" && (
            <p className="glossary-note">
              Definitions unavailable.{" "}
              <button type="button" className="glossary-retry" onClick={retry}>
                Retry
              </button>
            </p>
          )}
          {status === "ready" && total === 0 && (
            <p className="glossary-note">No glossary terms on this page.</p>
          )}
          {status === "ready" && total > 0 && shown === 0 && (
            <p className="glossary-note">No terms match “{filter.trim()}”.</p>
          )}
          {coreShown.length > 0 && (
            <section>
              <h3>On this page</h3>
              <ul>
                {coreShown.map((t) => (
                  <TermRow key={t.id} term={t} onOpen={setDialogId} />
                ))}
              </ul>
            </section>
          )}
          {foundGroups.length > 0 && (
            <section>
              <h3>Also mentioned</h3>
              {foundGroups.map((g) => (
                <div key={g.category}>
                  <h4>{CATEGORY_LABELS[g.category]}</h4>
                  <ul>
                    {g.terms.map((t) => (
                      <TermRow key={t.id} term={t} onOpen={setDialogId} />
                    ))}
                  </ul>
                </div>
              ))}
            </section>
          )}
        </div>
      {dialog}
      </div>
  );
}
