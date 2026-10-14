import { useEffect, useMemo, useState } from "react";
import { api } from "../../api";
import type { VerseRecord } from "./ch01/types";

/**
 * Fetch one chapter's verse text once, and expose it by verse range.
 *
 * Verse text is optional decoration: a failed fetch is reported through
 * `corpusError` and `textFor` then returns no text, so every card shows its
 * "verse text unavailable" note and still computes.
 */
export function useVerses(chapter: number) {
  const [verses, setVerses] = useState<Map<number, VerseRecord>>(new Map());
  const [corpusError, setCorpusError] = useState<unknown>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .corpusVerses(chapter)
      .then((result) => {
        if (cancelled) return;
        const list = (result as { verses: VerseRecord[] }).verses ?? [];
        setVerses(new Map(list.map((v) => [v.verse, v])));
      })
      .catch((err: unknown) => {
        if (!cancelled) setCorpusError(err);
      });
    return () => {
      cancelled = true;
    };
  }, [chapter]);

  /** Join the corpus text for a verse range like "31-33", gaps skipped. */
  const textFor = useMemo(
    () =>
      (range: string): { text: string | null; citations: string[] } => {
        const [start, end] = range.split("-").map(Number);
        const last = Number.isFinite(end) ? end : start;
        const found: VerseRecord[] = [];
        for (let n = start; n <= last; n += 1) {
          const record = verses.get(n);
          if (record?.translation_en) found.push(record);
        }
        if (found.length === 0) return { text: null, citations: [] };
        return {
          text: found.map((v) => v.translation_en.trim()).join("\n\n"),
          citations: found.map((v) => v.id),
        };
      },
    [verses],
  );

  return { corpusError, textFor };
}
