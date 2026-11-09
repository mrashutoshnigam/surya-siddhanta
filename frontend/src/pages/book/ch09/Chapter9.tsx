import { useEffect, useState } from "react";
import { api } from "../../../api";
import { DateInput } from "../../../components/Inputs";
import type { DateValue } from "../../../components/Inputs";
import { ErrorBox, PageHeader } from "../../../components/Tables";
import { VerseCard } from "../../../components/VerseCard";
import { useVerses } from "../useVerses";
import { V02Direction } from "./V02Direction";
import { V06Events } from "./V06Events";
import { V06Thresholds } from "./V06Thresholds";
import { V10NextEvent } from "./V10NextEvent";
import { V12Stars } from "./V12Stars";
import { PLANETS } from "./types";
import type { Chapter9Payload } from "./types";

/**
 * Chapter 9 of the book: the heliacal verses in order, for one planet and a
 * date. Place plays no part — the library ignores the observer for heliacal
 * events — so none is asked for.
 */
export function Chapter9() {
  const [planet, setPlanet] = useState<string>("Venus");
  const [date, setDate] = useState<DateValue>({ year: 2024, month: 1, day: 1 });
  const [months, setMonths] = useState(12);
  const [payload, setPayload] = useState<Chapter9Payload | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);
  const { corpusError, textFor } = useVerses(9);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api
      .bookChapter9({ planet, ...date, months })
      .then((result) => {
        if (!cancelled) {
          setPayload(result as Chapter9Payload);
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
  }, [planet, date.year, date.month, date.day, months]);

  /** The panel for one card id — the only place a card id maps to a component. */
  function panelFor(id: string) {
    if (!payload) return null;
    switch (id) {
      case "ix.2-3":
        return <V02Direction card={payload.cards["ix.2-3"]} />;
      case "ix.6-9":
        return <V06Thresholds card={payload.cards["ix.6-9"]} />;
      case "ix.10-11":
        return <V10NextEvent card={payload.cards["ix.10-11"]} />;
      case "ix.6-11":
        return <V06Events card={payload.cards["ix.6-11"]} />;
      case "ix.12-18":
        return <V12Stars card={payload.cards["ix.12-18"]} />;
      default:
        return null;
    }
  }

  return (
    <div className="book-page">
      <PageHeader
        title="Chapter 9 — Of Heliacal Risings and Settings"
        subtitle="Choose a planet and a date to explore when it disappears into the Sun's glare and becomes visible again under the model's visibility rules."
      />

      <div className="book-datebar">
        <div className="field-row">
          <label>
            Planet
            <select value={planet} onChange={(e) => setPlanet(e.target.value)}>
              {PLANETS.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </label>
          <label>
            Months ahead
            <input
              type="number"
              value={months}
              min={1}
              max={36}
              onChange={(e) => setMonths(Number(e.target.value))}
            />
          </label>
        </div>
        <DateInput value={date} onChange={setDate} />
        {loading && <span className="ss-note">computing…</span>}
      </div>

      <ErrorBox error={error} />
      {corpusError != null && (
        <p className="ss-note">
          The verse text could not be loaded. You can still use the calculations below.
        </p>
      )}

      {payload && (
        <div className="book-body">
          <nav className="verse-rail">
            {payload.order.map((id) => {
              const card = payload.cards[id as keyof typeof payload.cards];
              return (
                <a key={id} href={`#${id}`}>
                  <span className="verse-rail-ref">ix.{card.verses}</span>
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
                  prefix="ix"
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
              The calculations here apply the visibility limits directly to ecliptic
              elongation. They omit the conversions through ascensional equivalents
              described in verses 4-5, 11 and 16-17, which express the intervals and
              motions in degrees of time before converting back to the ecliptic.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
