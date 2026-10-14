import { useEffect, useState } from "react";
import { api } from "../../../api";
import { DateInput, DEFAULT_LATLON, LatLonInput } from "../../../components/Inputs";
import type { DateValue, LatLon } from "../../../components/Inputs";
import { ErrorBox, PageHeader } from "../../../components/Tables";
import { VerseCard } from "../../../components/VerseCard";
import { useVerses } from "../useVerses";
import { V42Sphere } from "./V42Sphere";
import { V59Earth } from "./V59Earth";
import { V63Limits } from "./V63Limits";
import { V70Clock } from "./V70Clock";
import { V74Days } from "./V74Days";
import { V78Regents } from "./V78Regents";
import { V80Orbits } from "./V80Orbits";
import type { Chapter12Payload } from "./types";

/**
 * Chapter 12 of the book: the cosmography verses in order, for a date and a
 * place. Most of the chapter states fixed dimensions, so each card says
 * whether the date or place moves it.
 */
export function Chapter12() {
  const [date, setDate] = useState<DateValue>({ year: 2024, month: 1, day: 1 });
  const [place, setPlace] = useState<LatLon>(DEFAULT_LATLON);
  const [payload, setPayload] = useState<Chapter12Payload | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);
  const { corpusError, textFor } = useVerses(12);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api
      .bookChapter12({ ...date, ...place })
      .then((result) => {
        if (!cancelled) {
          setPayload(result as Chapter12Payload);
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
      case "xii.42-44":
        return <V42Sphere card={payload.cards["xii.42-44"]} />;
      case "xii.59-61":
        return <V59Earth card={payload.cards["xii.59-61"]} />;
      case "xii.63-68":
        return <V63Limits card={payload.cards["xii.63-68"]} />;
      case "xii.70-71":
        return <V70Clock card={payload.cards["xii.70-71"]} />;
      case "xii.74":
        return <V74Days card={payload.cards["xii.74"]} />;
      case "xii.78-79":
        return <V78Regents card={payload.cards["xii.78-79"]} />;
      case "xii.80-90":
        return <V80Orbits card={payload.cards["xii.80-90"]} />;
      default:
        return null;
    }
  }

  return (
    <div className="book-page">
      <PageHeader
        title="Chapter 12 — Cosmogony, Geography, and Dimensions of the Creation"
        subtitle="The earth, the sphere and the orbits: fixed dimensions, with the place and date you choose moving only what they must."
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
                  <span className="verse-rail-ref">xii.{card.verses}</span>
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
                  prefix="xii"
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
              Not laid out: the creation, the elements, the seven patalas and Maya&apos;s nine
              questions (descriptive, nothing to compute; the Cosmography page lists them), and
              the verses after v.90 that describe rather than measure. Orbits are reckoned per
              kalpa, not per mahayuga.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
