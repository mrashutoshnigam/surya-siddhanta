import { useEffect, useMemo, useState } from "react";
import { useLocation } from "react-router-dom";
import { useGlossary } from "./GlossaryProvider";
import { matchTerms, routeKey } from "./matchTerms";
import type { TermEntry } from "./types";

/** How long the page must stay still before it is scanned again. */
const SCAN_DEBOUNCE_MS = 300;

/**
 * All text under `root`, one text node per line.
 *
 * `textContent` would glue neighbouring cells together ("RohiniMars"),
 * which defeats the whole-word match; walking text nodes keeps them apart.
 * SVG <text> is included, so chart labels count.
 */
function collectText(root: Node): string {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  const parts: string[] = [];
  for (let node = walker.nextNode(); node; node = walker.nextNode()) {
    if (node.nodeValue) parts.push(node.nodeValue);
  }
  return parts.join("\n");
}

/** True when two sorted id lists are identical. */
function sameIds(a: string[], b: string[]): boolean {
  return a.length === b.length && a.every((id, i) => id === b[i]);
}

/**
 * The glossary terms on the current page.
 *
 * `core` is the page's curated list, in the order the page presents them,
 * so it is there before any calculation runs. `found` is everything else a
 * scan of the rendered page turns up — result values, chat answers, chart
 * labels — sorted by name. The scan watches `main.content` for changes and
 * is torn down on every route change.
 */
export function useTermsOnPage(): { core: TermEntry[]; found: TermEntry[] } {
  const { index } = useGlossary();
  const { pathname } = useLocation();
  const [foundIds, setFoundIds] = useState<string[]>([]);

  useEffect(() => {
    const root = document.querySelector("main.content");
    if (!index || !root) return;
    let timer: number | undefined;

    const scan = () => {
      const ids = [...matchTerms(collectText(root), index, pathname)].sort();
      setFoundIds((prev) => (sameIds(prev, ids) ? prev : ids));
    };
    const schedule = () => {
      window.clearTimeout(timer);
      timer = window.setTimeout(scan, SCAN_DEBOUNCE_MS);
    };

    scan();
    const observer = new MutationObserver(schedule);
    observer.observe(root, { subtree: true, childList: true, characterData: true });
    return () => {
      observer.disconnect();
      window.clearTimeout(timer);
    };
  }, [index, pathname]);

  return useMemo(() => {
    if (!index) return { core: [], found: [] };
    const coreIds = index.routes[routeKey(pathname)] ?? [];
    const core = coreIds.flatMap((id) => index.terms.get(id) ?? []);
    const inCore = new Set(coreIds);
    const found = foundIds
      .filter((id) => !inCore.has(id))
      .flatMap((id) => index.terms.get(id) ?? [])
      .sort((a, b) => a.term.localeCompare(b.term));
    return { core, found };
  }, [index, pathname, foundIds]);
}
