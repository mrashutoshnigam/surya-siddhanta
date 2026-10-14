import { useEffect, useState } from "react";
import { api } from "../../../api";
import { DateInput, todayValue } from "../../../components/Inputs";
import type { DateValue } from "../../../components/Inputs";
import { ErrorBox, PageHeader } from "../../../components/Tables";
import { VerseCard } from "../../../components/VerseCard";
import { useVerses } from "../useVerses";
import { V01Direction } from "./V01Direction";
import { V05Gnomon } from "./V05Gnomon";
import { V09Ayana } from "./V09Ayana";
import { V13Latitude } from "./V13Latitude";
import { V18Equatorial } from "./V18Equatorial";
import { V21NoonShadow } from "./V21NoonShadow";
import { V38HourAngle } from "./V38HourAngle";
import { V42Cara } from "./V42Cara";
import { V43Rising } from "./V43Rising";
import type { Chapter3Payload } from "./types";

/**
 * Chapter 3 of the book: its computational verses in order, each with the
 * verse text above and a live panel below. Owns the date, the two fetches
 * and the verse rail; each card owns its own inputs.
 */
export function Chapter3() {
  const [date, setDate] = useState<DateValue>(todayValue());
  const [payload, setPayload] = useState<Chapter3Payload | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);
  const { corpusError, textFor } = useVerses(3);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api
      .bookChapter3({ ...date })
      .then((result) => {
        if (!cancelled) {
          setPayload(result as Chapter3Payload);
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
    const key = payload.jd;
    switch (id) {
      case "iii.1-4":
        return <V01Direction card={payload.cards["iii.1-4"]} />;
      case "iii.5-8":
        return <V05Gnomon card={payload.cards["iii.5-8"]} />;
      case "iii.9-12":
        return <V09Ayana card={payload.cards["iii.9-12"]} />;
      case "iii.13-17":
        return <V13Latitude key={key} card={payload.cards["iii.13-17"]} />;
      case "iii.18-20":
        return <V18Equatorial key={key} card={payload.cards["iii.18-20"]} />;
      case "iii.21-23":
        return <V21NoonShadow key={key} card={payload.cards["iii.21-23"]} />;
      case "iii.38-41":
        return <V38HourAngle key={key} card={payload.cards["iii.38-41"]} />;
      case "iii.42":
        return <V42Cara key={key} card={payload.cards["iii.42"]} />;
      case "iii.43-44":
        return <V43Rising card={payload.cards["iii.43-44"]} />;
      default:
        return null;
    }
  }

  return (
    <div className="book-page">
      <PageHeader
        title="Chapter 3 — Of Direction, Place and Time"
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
                  <span className="verse-rail-ref">iii.{card.verses}</span>
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
                  prefix="iii"
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
              Verses 46-51 (the rising sign, or lagna, and the time of night from it) are not
              laid out here: the library&apos;s lagna is not yet corrected, so showing it would
              show a wrong figure. Verses 24-37 and 45 are narrative or have no calculation in
              the library.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
