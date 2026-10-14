import { lazy, Suspense, useEffect, useMemo, useRef, useState } from "react";
import { useGlossary } from "./GlossaryProvider";
import { CATEGORY_LABELS, CATEGORY_ORDER, Category, TermEntry } from "./types";
import { useTermsOnPage } from "./useTermsOnPage";

/**
 * Viewport width at which the panel docks beside the page: sidebar 264 +
 * content max-width 1200 + panel 320. Any narrower and a docked column
 * would squeeze the page, so the panel becomes an overlay drawer instead.
 */
const DOCK_QUERY = "(min-width: 1784px)";

/**
 * The popup and KaTeX (its code, CSS and fonts) load together, on the first
 * term a reader opens, so no page pays for them up front.
 */
const TermDialog = lazy(() => import("./TermDialog").then((m) => ({ default: m.TermDialog })));

/** localStorage key remembering whether the docked panel is open. */
const STORAGE_KEY = "ss.glossary.open";

/** Whether the docked panel was left open; defaults to open. */
function storedDockedOpen(): boolean {
  try {
    return localStorage.getItem(STORAGE_KEY) !== "0";
  } catch {
    return true;
  }
}

/** Remember the docked panel's open state; storage failures are harmless. */
function storeDockedOpen(open: boolean): void {
  try {
    localStorage.setItem(STORAGE_KEY, open ? "1" : "0");
  } catch {
    /* storage blocked: the panel just forgets on reload */
  }
}

/** Live result of a CSS media query. */
function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() => window.matchMedia(query).matches);
  useEffect(() => {
    const list = window.matchMedia(query);
    const onChange = () => setMatches(list.matches);
    onChange();
    list.addEventListener("change", onChange);
    return () => list.removeEventListener("change", onChange);
  }, [query]);
  return matches;
}

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

/**
 * The right-hand glossary: every Surya Siddhanta term on the current page.
 *
 * Docked beside the page on wide screens (open state remembered), an
 * overlay drawer below that (always starts closed), full-screen on phones.
 * It sits outside `main.content`, so it never changes the page's layout
 * and its own updates never trigger the page scan.
 */
export function GlossaryPanel() {
  const { status, index, retry } = useGlossary();
  const { core, found } = useTermsOnPage();
  const docked = useMediaQuery(DOCK_QUERY);
  const [dockedOpen, setDockedOpen] = useState(storedDockedOpen);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [filter, setFilter] = useState("");
  const [dialogId, setDialogId] = useState<string | null>(null);
  const filterRef = useRef<HTMLInputElement>(null);
  const tabRef = useRef<HTMLButtonElement>(null);
  const open = docked ? dockedOpen : drawerOpen;

  function setOpen(next: boolean) {
    if (docked) {
      setDockedOpen(next);
      storeDockedOpen(next);
    } else {
      setDrawerOpen(next);
    }
    if (!next) requestAnimationFrame(() => tabRef.current?.focus());
  }

  // The drawer takes focus when it opens and closes on Escape, unless a
  // term popup is open — that popup handles its own Escape first.
  useEffect(() => {
    if (docked || !drawerOpen) return;
    filterRef.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !dialogId) setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [docked, drawerOpen, dialogId]);

  const query = filter.trim().toLowerCase();
  const coreShown = useMemo(() => core.filter((t) => termMatchesFilter(t, query)), [core, query]);
  const foundGroups = useMemo(
    () => groupByCategory(found.filter((t) => termMatchesFilter(t, query))),
    [found, query],
  );
  const total = core.length + found.length;
  const shown = coreShown.length + foundGroups.reduce((n, g) => n + g.terms.length, 0);

  const dialog = dialogId && index && (
    <Suspense fallback={null}>
      <TermDialog id={dialogId} index={index} onClose={() => setDialogId(null)} />
    </Suspense>
  );

  if (!open) {
    return (
      <button
        ref={tabRef}
        type="button"
        className="glossary-tab"
        aria-expanded={false}
        aria-controls="glossary-panel"
        onClick={() => setOpen(true)}
      >
        Terms <span className="glossary-count">{total}</span>
      </button>
    );
  }

  return (
    <>
      {!docked && <div className="glossary-backdrop" onClick={() => setOpen(false)} />}
      <aside
        id="glossary-panel"
        className={"glossary-panel " + (docked ? "is-docked" : "is-drawer")}
        aria-label="Glossary"
      >
        <header className="glossary-head">
          <h2>
            Terms on this page <span className="glossary-count">{total}</span>
          </h2>
          <button
            type="button"
            className="glossary-close"
            aria-label="Close glossary"
            onClick={() => setOpen(false)}
          >
            ×
          </button>
        </header>
        <input
          ref={filterRef}
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
      </aside>
      {dialog}
    </>
  );
}
