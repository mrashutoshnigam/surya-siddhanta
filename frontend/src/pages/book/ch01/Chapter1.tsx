import { useEffect, useMemo, useState } from "react";
import { api } from "../../../api";
import { DateInput, todayValue } from "../../../components/Inputs";
import type { DateValue } from "../../../components/Inputs";
import { ErrorBox, PageHeader } from "../../../components/Tables";
import { VerseCard } from "../../../components/VerseCard";
import { V11TimeUnits } from "./V11TimeUnits";
import { V15Yugas } from "./V15Yugas";
import { V23Epoch } from "./V23Epoch";
import { V29Bhagana } from "./V29Bhagana";
import { V35MeanRule } from "./V35MeanRule";
import { V41OrbitPoints } from "./V41OrbitPoints";
import { V48AharganaRoute } from "./V48AharganaRoute";
import { V52MeanPlaces } from "./V52MeanPlaces";
import { V52Vara } from "./V52Vara";
import { V55Samvatsara } from "./V55Samvatsara";
import { V56EpochPositions } from "./V56EpochPositions";
import type { Chapter1Payload, VerseRecord } from "./types";

/**
 * Chapter 1 of the book: its computational verses in order, each with the
 * verse text above and a live panel below.
 *
 * This component owns the page's date, the two fetches and the verse rail.
 * Each card owns its own inputs, and the date is the ground the card
 * sliders move away from.
 */
export function Chapter1() {
  const [date, setDate] = useState<DateValue>(todayValue());
  const [payload, setPayload] = useState<Chapter1Payload | null>(null);
  const [verses, setVerses] = useState<Map<number, VerseRecord>>(new Map());
  const [corpusError, setCorpusError] = useState<unknown>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);

  // The calculations: refetched whenever the date changes.
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api
      .bookChapter1(date)
      .then((result) => {
        if (!cancelled) {
          setPayload(result as Chapter1Payload);
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

  // The verse text: fetched once. It does not vary with the date, and its
  // absence must not stop a single calculation from rendering.
  useEffect(() => {
    let cancelled = false;
    api
      .corpusVerses(1)
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

  /** Join the corpus text for a verse range like "29-34", gaps skipped. */
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

  const cards = payload?.cards;

  /** The panel for one card id — the only place a card id maps to a component. */
  function panelFor(id: string) {
    if (!cards || !payload) return null;
    switch (id) {
      case "i.11-13":
        return <V11TimeUnits card={cards["i.11-13"]} />;
      case "i.15-22":
        return <V15Yugas card={cards["i.15-22"]} />;
      case "i.23-24":
        return <V23Epoch card={cards["i.23-24"]} />;
      case "i.29-34":
        return <V29Bhagana card={cards["i.29-34"]} />;
      case "i.35-37":
        return <V35MeanRule card={cards["i.35-37"]} rashis={payload.rashis} />;
      case "i.41-42":
        return <V41OrbitPoints card={cards["i.41-42"]} kind="apsis" rashis={payload.rashis} />;
      case "i.43-44":
        return <V41OrbitPoints card={cards["i.43-44"]} kind="node" rashis={payload.rashis} />;
      case "i.48-51":
        return <V48AharganaRoute card={cards["i.48-51"]} />;
      case "i.52-vara":
        return <V52Vara card={cards["i.52-vara"]} />;
      case "i.52-54":
        return <V52MeanPlaces card={cards["i.52-54"]} rashis={payload.rashis} />;
      case "i.55":
        return <V55Samvatsara card={cards["i.55"]} />;
      case "i.56-58":
        return <V56EpochPositions card={cards["i.56-58"]} />;
      default:
        return null;
    }
  }

  return (
    <div className="book-page">
      <PageHeader
        title="Chapter 1 — Of the Mean Motions of the Planets"
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
            {payload.order.map((id) => (
              <a key={id} href={`#${id}`}>
                <span className="verse-rail-ref">i.{payload.cards[id as keyof typeof payload.cards].verses}</span>
                {payload.cards[id as keyof typeof payload.cards].title}
              </a>
            ))}
          </nav>

          <div className="verse-cards">
            {payload.order.map((id) => {
              const card = payload.cards[id as keyof typeof payload.cards];
              const { text, citations } = textFor(card.verses);
              return (
                <VerseCard
                  key={id}
                  id={id}
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
          </div>
        </div>
      )}
    </div>
  );
}
