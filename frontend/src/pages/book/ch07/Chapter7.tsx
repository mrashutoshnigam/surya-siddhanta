import { useEffect, useState } from "react";
import { api } from "../../../api";
import { DateInput } from "../../../components/Inputs";
import type { DateValue } from "../../../components/Inputs";
import { ErrorBox, PageHeader } from "../../../components/Tables";
import { VerseCard } from "../../../components/VerseCard";
import { useVerses } from "../useVerses";
import { V01Who } from "./V01Who";
import { V02Direction } from "./V02Direction";
import { V04Correction } from "./V04Correction";
import { V12Latitudes } from "./V12Latitudes";
import { V19Classification } from "./V19Classification";
import { BODIES } from "./types";
import type { Body, Chapter7Payload } from "./types";

interface Example {
  label: string;
  one: Body;
  two: Body;
  date: DateValue;
  window: number;
}

/** Pairs that meet near a known date, so the cards have a conjunction to show. */
const EXAMPLES: Example[] = [
  { label: "Mars and Venus, Feb 2024", one: "Mars", two: "Venus", date: { year: 2024, month: 2, day: 1 }, window: 400 },
  { label: "Jupiter and Saturn, 2020", one: "Jupiter", two: "Saturn", date: { year: 2019, month: 12, day: 1 }, window: 800 },
];

/** A labelled body picker. */
function BodySelect({ label, value, onChange }: { label: string; value: Body; onChange: (b: Body) => void }) {
  return (
    <label>
      {label}
      <select value={value} onChange={(e) => onChange(e.target.value as Body)}>
        {BODIES.map((b) => (
          <option key={b} value={b}>
            {b}
          </option>
        ))}
      </select>
    </label>
  );
}

/**
 * Chapter 7 of the book: the conjunction verses in order, for a pair of
 * bodies and the conjunction nearest a date. The date is also where the hand
 * method of v.4-6 starts its repetition, so a date a little before a
 * conjunction shows it settle.
 */
export function Chapter7() {
  const [one, setOne] = useState<Body>(EXAMPLES[0].one);
  const [two, setTwo] = useState<Body>(EXAMPLES[0].two);
  const [date, setDate] = useState<DateValue>(EXAMPLES[0].date);
  const [window_, setWindow] = useState<number>(EXAMPLES[0].window);
  const [payload, setPayload] = useState<Chapter7Payload | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);
  const { corpusError, textFor } = useVerses(7);

  useEffect(() => {
    if (one === two) {
      setError(new Error("Choose two different bodies."));
      return undefined;
    }
    let cancelled = false;
    setLoading(true);
    api
      .bookChapter7({ planet1: one, planet2: two, ...date, search_days: window_ })
      .then((result) => {
        if (!cancelled) {
          setPayload(result as Chapter7Payload);
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
  }, [one, two, date.year, date.month, date.day, window_]);

  /** Load one of the example pairs. */
  function loadExample(e: Example) {
    setOne(e.one);
    setTwo(e.two);
    setDate(e.date);
    setWindow(e.window);
  }

  /** The panel for one card id — the only place a card id maps to a component. */
  function panelFor(id: string) {
    if (!payload) return null;
    switch (id) {
      case "vii.1":
        return <V01Who card={payload.cards["vii.1"]} />;
      case "vii.2-3":
        return <V02Direction card={payload.cards["vii.2-3"]} />;
      case "vii.4-6":
        return <V04Correction card={payload.cards["vii.4-6"]} />;
      case "vii.12":
        return <V12Latitudes card={payload.cards["vii.12"]} one={payload.pair[0]} two={payload.pair[1]} />;
      case "vii.19-22":
        return <V19Classification card={payload.cards["vii.19-22"]} />;
      default:
        return null;
    }
  }

  return (
    <div className="book-page">
      <PageHeader
        title="Chapter 7 — Of Planetary Conjunctions"
        subtitle="The verses of the chapter that compute something, for a pair of bodies and the conjunction nearest a date you choose."
      />

      <div className="book-datebar">
        <div className="field-row">
          <BodySelect label="First body" value={one} onChange={setOne} />
          <BodySelect label="Second body" value={two} onChange={setTwo} />
          <label>
            Search window (± days)
            <input
              type="number"
              value={window_}
              min={10}
              max={3700}
              onChange={(e) => setWindow(Number(e.target.value))}
            />
          </label>
        </div>
        <DateInput value={date} onChange={setDate} />
        {EXAMPLES.map((e) => (
          <button key={e.label} type="button" className="chip chip-button" onClick={() => loadExample(e)}>
            {e.label}
          </button>
        ))}
        {loading && <span className="ss-note">computing…</span>}
      </div>

      <ErrorBox error={error} />
      {corpusError != null && (
        <p className="ss-note">
          The verse corpus is not reachable, so the cards below show their calculations
          without the text.
        </p>
      )}

      {payload && one !== two && (
        <div className="book-body">
          <nav className="verse-rail">
            {payload.order.map((id) => {
              const card = payload.cards[id as keyof typeof payload.cards];
              return (
                <a key={id} href={`#${id}`}>
                  <span className="verse-rail-ref">vii.{card.verses}</span>
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
                  prefix="vii"
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
              Not laid out here: verses 7 to 10 (the corrections for meridian distance and
              declination), 13 and 14 (the diameters of the star-planets), 15 to 18 (the gnomon
              construction) and 24. The library has no calculation for them. The victor in an
              encounter is the northern planet; the further tests of brightness and size in
              v.20-22 are not modelled.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
