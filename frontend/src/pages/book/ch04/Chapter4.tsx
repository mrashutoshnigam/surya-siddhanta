import { useEffect, useState } from "react";
import { api } from "../../../api";
import { DateInput, todayValue } from "../../../components/Inputs";
import type { DateValue } from "../../../components/Inputs";
import { ErrorBox, PageHeader } from "../../../components/Tables";
import { VerseCard } from "../../../components/VerseCard";
import { useVerses } from "../useVerses";
import { V01Diameters } from "./V01Diameters";
import { V04Shadow } from "./V04Shadow";
import { V07Opposition } from "./V07Opposition";
import { V10Obscuration } from "./V10Obscuration";
import { V12Duration } from "./V12Duration";
import type { Chapter4Payload } from "./types";

/**
 * Chapter 4 of the book: the lunar-eclipse verses in order, evaluated for the
 * full moon nearest the chosen date. The date's day is only where the search
 * for the full moon starts.
 */
export function Chapter4() {
  const [date, setDate] = useState<DateValue>(todayValue());
  const [payload, setPayload] = useState<Chapter4Payload | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);
  const { corpusError, textFor } = useVerses(4);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api
      .bookChapter4({ ...date })
      .then((result) => {
        if (!cancelled) {
          setPayload(result as Chapter4Payload);
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

  /** The panel for one card id — the only place a card id maps to a component. */
  function panelFor(id: string) {
    if (!payload) return null;
    switch (id) {
      case "iv.1-2":
        return <V01Diameters card={payload.cards["iv.1-2"]} />;
      case "iv.4-5":
        return <V04Shadow card={payload.cards["iv.4-5"]} />;
      case "iv.7-8":
        return <V07Opposition card={payload.cards["iv.7-8"]} />;
      case "iv.10-11":
        return <V10Obscuration key={payload.jd} card={payload.cards["iv.10-11"]} />;
      case "iv.12-13":
        return <V12Duration key={payload.jd} card={payload.cards["iv.12-13"]} />;
      default:
        return null;
    }
  }

  return (
    <div className="book-page">
      <PageHeader
        title="Chapter 4 — Of Eclipses, and especially of Lunar Eclipses"
        subtitle="The verses of the chapter that compute something, for the full moon nearest a date you choose."
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
                  <span className="verse-rail-ref">iv.{card.verses}</span>
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
                  prefix="iv"
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
              Not laid out here: the contrary correction of the node (v.8), the repeated
              calculation of the duration (v.15), and verses 17-26 (immersion and emergence,
              the amount obscured at a given time, the deflection and the measure in digits).
              The library has no calculation for them yet.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
