import { useEffect, useState } from "react";
import { api } from "../../../api";
import { DateInput, DEFAULT_LATLON, LatLonInput } from "../../../components/Inputs";
import type { DateValue, LatLon } from "../../../components/Inputs";
import { ErrorBox, PageHeader } from "../../../components/Tables";
import { Picker, VerseCard } from "../../../components/VerseCard";
import { useVerses } from "../useVerses";
import { V02Circles } from "./V02Circles";
import { V04Directions } from "./V04Directions";
import { V10Obscuration } from "./V10Obscuration";
import { V13Visibility } from "./V13Visibility";
import { V14Path } from "./V14Path";
import { V17Stick } from "./V17Stick";
import { V20Immersion } from "./V20Immersion";
import { V23Colours } from "./V23Colours";
import type { Chapter6Payload, Kind } from "./types";

/** A dated eclipse of each kind at Ujjain in the SS reckoning, so the figure has something to show. */
const EXAMPLES: Record<Kind, DateValue> = {
  lunar: { year: 2026, month: 3, day: 15 },
  solar: { year: 2024, month: 10, day: 1 },
};

/**
 * Chapter 6 of the book: the projection of an eclipse, step by step, for the
 * full moon (lunar) or new moon (solar) nearest the chosen date at the
 * chosen place. The date's day is only where the search starts.
 */
export function Chapter6() {
  const [kind, setKind] = useState<Kind>("lunar");
  const [date, setDate] = useState<DateValue>(EXAMPLES.lunar);
  const [place, setPlace] = useState<LatLon>(DEFAULT_LATLON);
  const [payload, setPayload] = useState<Chapter6Payload | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);
  const { corpusError, textFor } = useVerses(6);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api
      .bookChapter6({ kind, ...date, ...place })
      .then((result) => {
        if (!cancelled) {
          setPayload(result as Chapter6Payload);
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
  }, [kind, date.year, date.month, date.day, place.latitude, place.longitude]);

  /** Switching kind also moves to a date that has an eclipse of that kind. */
  function chooseKind(next: Kind) {
    setKind(next);
    setDate(EXAMPLES[next]);
  }

  /** The panel for one card id — the only place a card id maps to a component. */
  function panelFor(id: string) {
    if (!payload) return null;
    const key = `${payload.kind}-${payload.jd}`;
    switch (id) {
      case "vi.2":
        return <V02Circles card={payload.cards["vi.2"]} />;
      case "vi.4-9":
        return <V04Directions card={payload.cards["vi.4-9"]} />;
      case "vi.10-11":
        return <V10Obscuration card={payload.cards["vi.10-11"]} />;
      case "vi.13":
        return <V13Visibility card={payload.cards["vi.13"]} />;
      case "vi.14-16":
        return <V14Path card={payload.cards["vi.14-16"]} />;
      case "vi.17-19":
        return <V17Stick key={key} card={payload.cards["vi.17-19"]} />;
      case "vi.20-22":
        return <V20Immersion card={payload.cards["vi.20-22"]} />;
      case "vi.23":
        return <V23Colours card={payload.cards["vi.23"]} />;
      default:
        return null;
    }
  }

  return (
    <div className="book-page">
      <PageHeader
        title="Chapter 6 — Of the Projection of Eclipses"
        subtitle="Build an eclipse diagram step by step. Choose a date and place, then follow the circles, contact points and path for the nearest eclipse."
      />

      <div className="book-datebar">
        <Picker
          value={kind}
          options={[
            { value: "lunar", label: "Lunar eclipse" },
            { value: "solar", label: "Solar eclipse" },
          ]}
          onChange={chooseKind}
        />
        <DateInput value={date} onChange={setDate} />
        <LatLonInput value={place} onChange={setPlace} />
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
                  <span className="verse-rail-ref">vi.{card.verses}</span>
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
                  prefix="vi"
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
              Verses 3 and 16 are missing from the available verse text; the closing
              admonition in verse 24 has no card. The diagram uses a straight chord
              for the path, and the duration calculation is not repeated to refine it.
              These choices can give slightly different results from the book.
              Contact and latitude directions follow verses 4 and 8.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
