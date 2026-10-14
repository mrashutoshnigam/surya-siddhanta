import type { GlossaryDoc, TermEntry } from "./types";

/**
 * Everything the page scan needs, built once per glossary load.
 *
 * Names are split by case mode: most terms match whatever the case, but a
 * few (a planet name that is also an everyday word, say) opt into exact
 * case. Each mode gets one alternation regex and one name → id map.
 */
export interface TermIndex {
  terms: Map<string, TermEntry>;
  routes: Record<string, string[]>;
  /** Exact name → id, for case-sensitive terms. */
  exact: Map<string, string>;
  /** Lower-cased name → id, for everything else. */
  folded: Map<string, string>;
  sensitive: RegExp | null;
  insensitive: RegExp | null;
}

/** Collapse runs of whitespace so "Purva\n Ashadha" keys like "Purva Ashadha". */
function squash(text: string): string {
  return text.replace(/\s+/g, " ").trim();
}

/** Escape a name for use inside a regex, letting any space match any whitespace. */
function toPattern(name: string): string {
  return name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&").replace(/ /g, "\\s+");
}

/**
 * One regex matching any of `names` as a whole word.
 *
 * Longest names come first so "mean longitude" wins over "longitude".
 * Word edges are Unicode lookarounds rather than `\b`, which treats
 * letters such as "ā" as non-word characters.
 */
function compile(names: string[], flags: string): RegExp | null {
  if (names.length === 0) return null;
  const body = [...names].sort((a, b) => b.length - a.length).map(toPattern).join("|");
  return new RegExp(`(?<![\\p{L}\\p{N}])(?:${body})(?![\\p{L}\\p{N}])`, flags);
}

/** Build the lookup maps and scan regexes for a glossary document. */
export function buildIndex(doc: GlossaryDoc): TermIndex {
  const terms = new Map<string, TermEntry>();
  const exact = new Map<string, string>();
  const folded = new Map<string, string>();
  for (const [id, term] of Object.entries(doc.terms)) {
    terms.set(id, { ...term, id });
    for (const raw of [term.term, ...(term.aliases ?? [])]) {
      const name = squash(raw);
      if (term.match?.caseSensitive) exact.set(name, id);
      else folded.set(name.toLowerCase(), id);
    }
  }
  return {
    terms,
    routes: doc.routes,
    exact,
    folded,
    sensitive: compile([...exact.keys()], "gu"),
    insensitive: compile([...folded.keys()], "giu"),
  };
}

/** The key a pathname is listed under in `routes` ("/moon/" → "/moon"). */
export function routeKey(pathname: string): string {
  return pathname.length > 1 ? pathname.replace(/\/+$/, "") : pathname;
}

/** True when a term may be reported on this route. */
function allowedOn(term: TermEntry, route: string): boolean {
  const routes = term.match?.routes;
  return !routes || routes.includes(route);
}

/**
 * The ids of every glossary term named in `text`, as seen on `pathname`.
 *
 * Pure: no DOM access, so it can be unit-tested with plain strings.
 */
export function matchTerms(text: string, index: TermIndex, pathname: string): Set<string> {
  const route = routeKey(pathname);
  const found = new Set<string>();
  const scan = (re: RegExp | null, lookup: Map<string, string>, fold: boolean) => {
    if (!re) return;
    for (const m of text.matchAll(re)) {
      const key = fold ? squash(m[0]).toLowerCase() : squash(m[0]);
      const id = lookup.get(key);
      const term = id ? index.terms.get(id) : undefined;
      if (id && term && allowedOn(term, route)) found.add(id);
    }
  };
  scan(index.sensitive, index.exact, false);
  scan(index.insensitive, index.folded, true);
  return found;
}
