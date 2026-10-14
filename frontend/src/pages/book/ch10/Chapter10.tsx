import { useEffect, useState } from "react";
import { api } from "../../../api";
import { DateInput, DEFAULT_LATLON, LatLonInput } from "../../../components/Inputs";
import type { DateValue, LatLon } from "../../../components/Inputs";
import { ErrorBox, PageHeader } from "../../../components/Tables";
import { VerseCard } from "../../../components/VerseCard";
import { useVerses } from "../useVerses";
import { V01Visibility } from "./V01Visibility";
import { V02RiseSet } from "./V02RiseSet";
import { V09Illumination } from "./V09Illumination";
import { V10Figure } from "./V10Figure";
import type { Chapter10Payload } from "./types";

/**
 * Chapter 10 of the book: the Moon's visibility, rising and setting, lit part
 * and figure, for a date and a place.
 */
export function Chapter10() {
  const [date, setDate] = useState<DateValue>({ year: 2024, month: 10, day: 5 });
  const [place, setPlace] = useState<LatLon>(DEFAULT_LATLON);
  const [payload, setPayload] = useState<Chapter10Payload | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);
  const { corpusError, textFor } = useVerses(10);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api
      .bookChapter10({ ...date, ...place })
      .then((result) => {
        if (!cancelled) {
          setPayload(result as Chapter10Payload);
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
      case "x.1":
        return <V01Visibility card={payload.cards["x.1"]} />;
      case "x.2-5":
        return <V02RiseSet card={payload.cards["x.2-5"]} />;
      case "x.9":
        return <V09Illumination card={payload.cards["x.9"]} />;
      case "x.10-14":
        return <V10Figure card={payload.cards["x.10-14"]} />;
      default:
        return null;
    }
  }

  return (
    <div className="book-page">
      <PageHeader
        title="Chapter 10 — Of the Moon's Rising and Setting, and of her Cusps"
        subtitle="When the Moon is seen, how much of her is lit, and how her cusps stand, for a date and a place you choose."
      />

      <div className="book-datebar">
        <DateInput value={date} onChange={setDate} />
        <LatLonInput value={place} onChange={setPlace} />
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
                  <span className="verse-rail-ref">x.{card.verses}</span>
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
                  prefix="x"
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
              Not laid out: v.2-5 (the Moon's setting after the Sun by repeated intervals in
              respirations) and v.6-8 (the elevation of the cusps from the declinations and the
              noon shadow). The library has no function for them, and v.10-14 are shown as the
              library's bright-limb and horn angles rather than the verses' construction.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
