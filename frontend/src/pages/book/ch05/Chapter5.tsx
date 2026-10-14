import { useEffect, useState } from "react";
import { api } from "../../../api";
import { DateInput, DEFAULT_LATLON, LatLonInput } from "../../../components/Inputs";
import type { DateValue, LatLon } from "../../../components/Inputs";
import { ErrorBox, PageHeader } from "../../../components/Tables";
import { VerseCard } from "../../../components/VerseCard";
import { useVerses } from "../useVerses";
import { V01NoParallax } from "./V01NoParallax";
import { V03Lagna } from "./V03Lagna";
import { V05Drkksepa } from "./V05Drkksepa";
import { V08Lambana } from "./V08Lambana";
import { V10Nati } from "./V10Nati";
import { V13Result } from "./V13Result";
import { V15Contacts } from "./V15Contacts";
import type { Chapter5Payload } from "./types";

/** A partial solar eclipse at Ujjain in the SS reckoning, so the eclipse cards have something to show. */
const EXAMPLE: DateValue = { year: 2024, month: 10, day: 1 };

/**
 * Chapter 5 of the book: the solar-eclipse parallax verses in order,
 * evaluated for the new moon nearest the chosen date at the chosen place.
 * The date's day is only where the search for the new moon starts.
 */
export function Chapter5() {
  const [date, setDate] = useState<DateValue>(EXAMPLE);
  const [place, setPlace] = useState<LatLon>(DEFAULT_LATLON);
  const [payload, setPayload] = useState<Chapter5Payload | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);
  const { corpusError, textFor } = useVerses(5);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api
      .bookChapter5({ ...date, ...place })
      .then((result) => {
        if (!cancelled) {
          setPayload(result as Chapter5Payload);
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
  }, [date.year, date.month, date.day, place.latitude, place.longitude]);

  /** The panel for one card id — the only place a card id maps to a component. */
  function panelFor(id: string) {
    if (!payload) return null;
    switch (id) {
      case "v.1":
        return <V01NoParallax card={payload.cards["v.1"]} />;
      case "v.3-4":
        return <V03Lagna card={payload.cards["v.3-4"]} />;
      case "v.5-7":
        return <V05Drkksepa card={payload.cards["v.5-7"]} />;
      case "v.8-9":
        return <V08Lambana key={payload.jd} card={payload.cards["v.8-9"]} />;
      case "v.10-12":
        return <V10Nati key={payload.jd} card={payload.cards["v.10-12"]} />;
      case "v.13":
        return <V13Result card={payload.cards["v.13"]} />;
      case "v.15-17":
        return <V15Contacts card={payload.cards["v.15-17"]} />;
      default:
        return null;
    }
  }

  return (
    <div className="book-page">
      <PageHeader
        title="Chapter 5 — Of Parallax in a Solar Eclipse"
        subtitle="The verses of the chapter that compute something, for the new moon nearest a date you choose, seen from a place you choose."
      />

      <div className="book-datebar">
        <DateInput value={date} onChange={setDate} />
        <LatLonInput value={place} onChange={setPlace} />
        <button type="button" className="chip chip-button" onClick={() => setDate(EXAMPLE)}>
          A solar eclipse: Oct 2024
        </button>
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
                  <span className="verse-rail-ref">v.{card.verses}</span>
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
                  prefix="v"
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
              Not laid out here: verses 2 and 14 (absent from the corpus) and verse 18. The
              library does not repeat the calculation until the parallax settles (v.9), and
              takes mean diameters, so figures differ slightly from the book's worked method.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
