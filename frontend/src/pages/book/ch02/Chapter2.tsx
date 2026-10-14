import { useEffect, useMemo, useState } from "react";
import { api } from "../../../api";
import { DateInput, todayValue } from "../../../components/Inputs";
import type { DateValue } from "../../../components/Inputs";
import { ErrorBox, PageHeader } from "../../../components/Tables";
import { VerseCard } from "../../../components/VerseCard";
import { V15SineTable } from "./V15SineTable";
import { V29BhujaKoti } from "./V29BhujaKoti";
import { V31Interpolation } from "./V31Interpolation";
import { V34Epicycles } from "./V34Epicycles";
import { V39Manda } from "./V39Manda";
import { V40Sighra } from "./V40Sighra";
import { V43TruePlace } from "./V43TruePlace";
import { V60DayLength } from "./V60DayLength";
import { V65Yoga } from "./V65Yoga";
import { V66Tithi } from "./V66Tithi";
import { V67Karana } from "./V67Karana";
import type { Chapter2Payload, VerseRecord } from "./types";

/**
 * Chapter 2 of the book: its computational verses in order, each with the
 * verse text above and a live panel below. Owns the date, the
 * two fetches and the verse rail; each card owns its own inputs.
 */
export function Chapter2() {
  const [date, setDate] = useState<DateValue>(todayValue());
  const [payload, setPayload] = useState<Chapter2Payload | null>(null);
  const [verses, setVerses] = useState<Map<number, VerseRecord>>(new Map());
  const [corpusError, setCorpusError] = useState<unknown>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api
      .bookChapter2({ ...date })
      .then((result) => {
        if (!cancelled) {
          setPayload(result as Chapter2Payload);
          setError(null);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [date.year, date.month, date.day]);

  useEffect(() => {
    let cancelled = false;
    api
      .corpusVerses(2)
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
  }, []);

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

  /** The panel for one card id — the only place a card id maps to a component. */
  function panelFor(id: string) {
    if (!payload) return null;
    switch (id) {
      case "ii.15-27":
        return <V15SineTable card={payload.cards["ii.15-27"]} />;
      case "ii.29-30":
        return <V29BhujaKoti card={payload.cards["ii.29-30"]} />;
      case "ii.31-33":
        return <V31Interpolation card={payload.cards["ii.31-33"]} />;
      case "ii.34-38":
        return <V34Epicycles card={payload.cards["ii.34-38"]} />;
      case "ii.39":
        return <V39Manda card={payload.cards["ii.39"]} />;
      case "ii.40-42":
        return <V40Sighra card={payload.cards["ii.40-42"]} />;
      case "ii.43-45":
        return <V43TruePlace card={payload.cards["ii.43-45"]} />;
      case "ii.60-63":
        return <V60DayLength key={payload.jd} card={payload.cards["ii.60-63"]} />;
      case "ii.65":
        return <V65Yoga card={payload.cards["ii.65"]} />;
      case "ii.66":
        return <V66Tithi card={payload.cards["ii.66"]} />;
      case "ii.67-69":
        return <V67Karana card={payload.cards["ii.67-69"]} />;
      default:
        return null;
    }
  }

  return (
    <div className="book-page">
      <PageHeader
        title="Chapter 2 — Of the True Places of the Planets"
        subtitle="The verses of the chapter that compute something, each with its own reckoning for a date you choose."
      />

      <div className="book-datebar">
        <DateInput value={date} onChange={setDate} />
        {loading && <span className="ss-note">computing…</span>}
      </div>

      <ErrorBox error={error} />
      {corpusError != null && (
        <p className="ss-note">
          The verse corpus is not reachable, so the cards below show their calculations
          without the text.
        </p>
      )}

      {payload && (
        <div className="book-body">
          <nav className="verse-rail">
            {payload.order.map((id) => {
              const card = payload.cards[id as keyof typeof payload.cards];
              return (
                <a key={id} href={`#${id}`}>
                  <span className="verse-rail-ref">ii.{card.verses}</span>
                  {card.title}
                </a>
              );
            })}
          </nav>

          <div className="verse-cards">
            {payload.order.map((id) => {
              const card = payload.cards[id as keyof typeof payload.cards];
              const { text, citations } = textFor(card.verses);
              return (
                <VerseCard
                  key={id}
                  id={id}
                  prefix="ii"
                  verses={card.verses}
                  title={card.title}
                  does={card.does}
                  dateDependent={card.date_dependent}
                  text={text}
                  citations={citations}
                >
                  {panelFor(id)}
                </VerseCard>
              );
            })}
            <p className="ss-note">
              Verses 1-14 (the causes of the irregularities), 46-53 (the correction of the
              daily motion, and the retrogradation) and 56-58 (the node and the latitude)
              are not laid out here: the first are narrative, the rest have no calculation
              in the library yet.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
