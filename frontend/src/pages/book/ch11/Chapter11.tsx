import { useEffect, useState } from "react";
import { api } from "../../../api";
import { DateInput } from "../../../components/Inputs";
import type { DateValue } from "../../../components/Inputs";
import { ErrorBox, PageHeader } from "../../../components/Tables";
import { VerseCard } from "../../../components/VerseCard";
import { useVerses } from "../useVerses";
import { V02SumRule } from "./V02SumRule";
import { V04Declination } from "./V04Declination";
import { V12Timing } from "./V12Timing";
import { V19Events } from "./V19Events";
import type { Chapter11Payload } from "./types";

/**
 * Chapter 11 of the book: the pata verses in order, for a date and a search
 * window. Place plays no part — the library takes no observer for a pata —
 * so none is asked for, as in Chapter 9.
 */
export function Chapter11() {
  const [date, setDate] = useState<DateValue>({ year: 2024, month: 1, day: 1 });
  const [days, setDays] = useState(60);
  const [payload, setPayload] = useState<Chapter11Payload | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);
  const { corpusError, textFor } = useVerses(11);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api
      .bookChapter11({ ...date, days })
      .then((result) => {
        if (!cancelled) {
          setPayload(result as Chapter11Payload);
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
  }, [date.year, date.month, date.day, days]);

  /** The panel for one card id — the only place a card id maps to a component. */
  function panelFor(id: string) {
    if (!payload) return null;
    switch (id) {
      case "xi.2-3":
        return <V02SumRule card={payload.cards["xi.2-3"]} />;
      case "xi.4-11":
        return <V04Declination card={payload.cards["xi.4-11"]} />;
      case "xi.12-14":
        return <V12Timing card={payload.cards["xi.12-14"]} />;
      case "xi.19":
        return <V19Events card={payload.cards["xi.19"]} />;
      default:
        return null;
    }
  }

  return (
    <div className="book-page">
      <PageHeader
        title="Chapter 11 — Of certain malignant Aspects of the Sun and Moon"
        subtitle="Vyatipata and Vaidhrita: when the Sun and Moon share a declination, for a date and a search window you choose."
      />

      <div className="book-datebar">
        <div className="field-row">
          <label>
            Days ahead
            <input
              type="number"
              value={days}
              min={1}
              max={365}
              onChange={(e) => setDays(Number(e.target.value))}
            />
          </label>
        </div>
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
                  <span className="verse-rail-ref">xi.{card.verses}</span>
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
                  prefix="xi"
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
              Not laid out: v.4-5 and v.16-18 (the pata's character and effects, nothing to
              compute), v.11's own equation applied to the Moon's node, and v.20-23 (a third
              yoga counted by asterism-portion, and the asterism-junction points to avoid). The
              library has no function for the nakshatra-related verses, and this chapter
              already shares its name with a different yoga in Chapter 1 — see the note above.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
