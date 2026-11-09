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
        subtitle="Choose a date and place to explore the Moon's rising and setting, the illuminated part of its disk and the tilt of its crescent."
      />

      <div className="book-datebar">
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
              The repeated setting-interval calculation in verses 2-5 and the
              cusp-elevation construction in verses 6-8 are not implemented here.
              The rise and set times come from the app's calculation model. The figure
              for verses 10-14 uses its bright-limb and horn angles rather than the
              construction given in those verses.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
