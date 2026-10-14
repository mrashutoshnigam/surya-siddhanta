import { useEffect, useState } from "react";
import { api } from "../../../api";
import { DateInput, DEFAULT_LATLON, LatLonInput } from "../../../components/Inputs";
import type { DateValue, LatLon } from "../../../components/Inputs";
import { ErrorBox, PageHeader } from "../../../components/Tables";
import { VerseCard } from "../../../components/VerseCard";
import { useVerses } from "../useVerses";
import { V04Hoops } from "./V04Hoops";
import { V10Points } from "./V10Points";
import { V13Lagnas } from "./V13Lagnas";
import { V14Sines } from "./V14Sines";
import { V20Time } from "./V20Time";
import type { Chapter13Payload } from "./types";

/**
 * Chapter 13 of the book: the armillary sphere and the instruments, for a
 * date, a place and a gnomon's shadow. The 3D sphere is on the Instruments
 * page; these cards give the numbers behind it.
 */
export function Chapter13() {
  const [date, setDate] = useState<DateValue>({ year: 2024, month: 1, day: 1 });
  const [place, setPlace] = useState<LatLon>(DEFAULT_LATLON);
  const [shadow, setShadow] = useState(20);
  const [forenoon, setForenoon] = useState(true);
  const [payload, setPayload] = useState<Chapter13Payload | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);
  const { corpusError, textFor } = useVerses(13);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api
      .bookChapter13({ ...date, ...place, shadow, forenoon })
      .then((result) => {
        if (!cancelled) {
          setPayload(result as Chapter13Payload);
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
  }, [date.year, date.month, date.day, place.latitude, place.longitude, shadow, forenoon]);

  /** The panel for one card id — the only place a card id maps to a component. */
  function panelFor(id: string) {
    if (!payload) return null;
    switch (id) {
      case "xiii.4-9":
        return <V04Hoops card={payload.cards["xiii.4-9"]} />;
      case "xiii.10-11":
        return <V10Points card={payload.cards["xiii.10-11"]} />;
      case "xiii.13-14":
        return <V13Lagnas card={payload.cards["xiii.13-14"]} />;
      case "xiii.14-15":
        return <V14Sines card={payload.cards["xiii.14-15"]} />;
      case "xiii.20-24":
        return <V20Time card={payload.cards["xiii.20-24"]} />;
      default:
        return null;
    }
  }

  return (
    <div className="book-page">
      <PageHeader
        title="Chapter 13 — Of the Armillary Sphere and other Instruments"
        subtitle="The hoops, the lagnas and the instruments of time, for a date, a place and a gnomon's shadow you choose."
      />

      <div className="book-datebar">
        <DateInput value={date} onChange={setDate} />
        <LatLonInput value={place} onChange={setPlace} />
        <div className="field-row">
          <label>
            Gnomon shadow (digits of 12)
            <input
              type="number"
              value={shadow}
              min={0}
              step={0.5}
              onChange={(e) => setShadow(Number(e.target.value))}
            />
          </label>
          <label>
            <input
              type="checkbox"
              checked={forenoon}
              onChange={(e) => setForenoon(e.target.checked)}
            />{" "}
            Before noon
          </label>
        </div>
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
                  <span className="verse-rail-ref">xiii.{card.verses}</span>
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
                  prefix="xiii"
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
              Not laid out: v.1-3, 16-19 and 21-22 (building and caring for the sphere, the seven
              sages), which have nothing to compute. The 3D sphere is on the Instruments page.
              Only the gnomon is the text&apos;s own; the wheel, arc, staff and the clepsydra&apos;s
              dimensions come from Burgess&apos;s notes.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
