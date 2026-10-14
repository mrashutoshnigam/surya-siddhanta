import { useEffect, useState } from "react";
import { api } from "../../../api";
import { DateInput, DEFAULT_LATLON, LatLonInput } from "../../../components/Inputs";
import type { DateValue, LatLon } from "../../../components/Inputs";
import { ErrorBox, PageHeader } from "../../../components/Tables";
import { VerseCard } from "../../../components/VerseCard";
import { useVerses } from "../useVerses";
import { V01Longitudes } from "./V01Longitudes";
import { V05Latitudes } from "./V05Latitudes";
import { V09Position } from "./V09Position";
import { V14Conjunctions } from "./V14Conjunctions";
import type { Chapter8Payload } from "./types";

/** The twenty-seven junction-stars, in the order of the zodiac. */
const STARS = [
  "Ashvini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu",
  "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta",
  "Chitra", "Svati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
  "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
  "Uttara Bhadrapada", "Revati",
];
const PLANETS = ["Mars", "Mercury", "Jupiter", "Venus", "Saturn"];

/**
 * Chapter 8 of the book: the polar longitudes derived from the verses'
 * shares, the latitudes, and one chosen star placed on a date. The
 * corpus numbers this chapter out of step with the verses, so each card
 * names the records that hold its text (or none).
 */
export function Chapter8() {
  const [star, setStar] = useState("Rohini");
  const [planet, setPlanet] = useState("Jupiter");
  const [date, setDate] = useState<DateValue>({ year: 2024, month: 1, day: 1 });
  const [months, setMonths] = useState(12);
  const [place, setPlace] = useState<LatLon>(DEFAULT_LATLON);
  const [payload, setPayload] = useState<Chapter8Payload | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);
  const { corpusError, textFor } = useVerses(8);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api
      .bookChapter8({ star, planet, ...date, months, ...place })
      .then((result) => {
        if (!cancelled) {
          setPayload(result as Chapter8Payload);
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
  }, [star, planet, date.year, date.month, date.day, months, place.latitude, place.longitude]);

  /** The panel for one card id — the only place a card id maps to a component. */
  function panelFor(id: string) {
    if (!payload) return null;
    switch (id) {
      case "viii.1-4":
        return <V01Longitudes card={payload.cards["viii.1-4"]} />;
      case "viii.5-9":
        return <V05Latitudes card={payload.cards["viii.5-9"]} />;
      case "viii.1-9":
        return <V09Position card={payload.cards["viii.1-9"]} />;
      case "viii.14-15":
        return <V14Conjunctions card={payload.cards["viii.14-15"]} />;
      default:
        return null;
    }
  }

  return (
    <div className="book-page">
      <PageHeader
        title="Chapter 8 — Of the Stars"
        subtitle="The positions of the twenty-seven junction-stars from the verses' own figures, and one star placed on a date you choose."
      />

      <div className="book-datebar">
        <div className="field-row">
          <label>
            Star
            <select value={star} onChange={(e) => setStar(e.target.value)}>
              {STARS.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </label>
          <label>
            Planet (for v.14-15)
            <select value={planet} onChange={(e) => setPlanet(e.target.value)}>
              {PLANETS.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </label>
          <label>
            Months searched
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
                  <span className="verse-rail-ref">viii.{card.verses}</span>
                  {card.title}
                </a>
              );
            })}
          </nav>

          <div className="verse-cards">
            {payload.order.map((id) => {
              const card = payload.cards[id as keyof typeof payload.cards];
              const { text, citations } = card.text_verses
                ? textFor(card.text_verses)
                : { text: null, citations: [] };
              return (
                <VerseCard
                  key={id}
                  id={id}
                  prefix="viii"
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
              The corpus export numbers this chapter out of step with the verses: its records
              after 8.5 carry the translator's notes on the names, not verses 6 to 28. Where
              a card shows no verse text, that is why. The table cards read the shares and
              latitudes from the records that hold them; the applied cards compute from the
              library. The library reads each latitude as ecliptic; the verses call it polar.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
