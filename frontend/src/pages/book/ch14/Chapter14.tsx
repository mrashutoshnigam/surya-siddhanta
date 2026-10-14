import { useEffect, useState } from "react";
import { api } from "../../../api";
import { DateInput } from "../../../components/Inputs";
import type { DateValue } from "../../../components/Inputs";
import { ErrorBox, PageHeader } from "../../../components/Tables";
import { VerseCard } from "../../../components/VerseCard";
import { useVerses } from "../useVerses";
import { V01Manas } from "./V01Manas";
import { V04Mukhas } from "./V04Mukhas";
import { V07Year } from "./V07Year";
import { V12Fathers } from "./V12Fathers";
import { V15Months } from "./V15Months";
import { V17Jupiter } from "./V17Jupiter";
import { V18Converter } from "./V18Converter";
import type { Chapter14Payload } from "./types";

const MANAS = [
  "brahma", "daiva", "pitrya", "prajapatya", "barhaspatya",
  "saura", "savana", "candra", "naksatra",
];

/**
 * Chapter 14 of the book: the modes of reckoning time, for a date, a
 * conversion between the nine modes and a choice of Jupiter method. Place
 * plays no part, so none is asked for.
 */
export function Chapter14() {
  const [date, setDate] = useState<DateValue>({ year: 2024, month: 1, day: 1 });
  const [value, setValue] = useState(1);
  const [fromMana, setFromMana] = useState("daiva");
  const [toMana, setToMana] = useState("savana");
  const [heliacal, setHeliacal] = useState(false);
  const [payload, setPayload] = useState<Chapter14Payload | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);
  const { corpusError, textFor } = useVerses(14);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api
      .bookChapter14({ ...date, value, from_mana: fromMana, to_mana: toMana, heliacal })
      .then((result) => {
        if (!cancelled) {
          setPayload(result as Chapter14Payload);
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
  }, [date.year, date.month, date.day, value, fromMana, toMana, heliacal]);

  /** The panel for one card id — the only place a card id maps to a component. */
  function panelFor(id: string) {
    if (!payload) return null;
    switch (id) {
      case "xiv.1-2":
        return <V01Manas card={payload.cards["xiv.1-2"]} />;
      case "xiv.4-6":
        return <V04Mukhas card={payload.cards["xiv.4-6"]} />;
      case "xiv.7-11":
        return <V07Year card={payload.cards["xiv.7-11"]} />;
      case "xiv.12-14":
        return <V12Fathers card={payload.cards["xiv.12-14"]} />;
      case "xiv.15-16":
        return <V15Months card={payload.cards["xiv.15-16"]} />;
      case "xiv.17":
        return <V17Jupiter card={payload.cards["xiv.17"]} />;
      case "xiv.18-21":
        return <V18Converter card={payload.cards["xiv.18-21"]} />;
      default:
        return null;
    }
  }

  return (
    <div className="book-page">
      <PageHeader
        title="Chapter 14 — Of the Different Modes of Reckoning Time"
        subtitle="The nine modes of time, the solar year, the Fathers' day and Jupiter's cycle, for a date you choose."
      />

      <div className="book-datebar">
        <DateInput value={date} onChange={setDate} />
        <div className="field-row">
          <label>
            Convert
            <input
              type="number"
              value={value}
              min={0}
              step="any"
              onChange={(e) => setValue(Number(e.target.value))}
            />
          </label>
          <label>
            from
            <select value={fromMana} onChange={(e) => setFromMana(e.target.value)}>
              {MANAS.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </label>
          <label>
            to
            <select value={toMana} onChange={(e) => setToMana(e.target.value)}>
              {MANAS.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </label>
          <label>
            <input
              type="checkbox"
              checked={heliacal}
              onChange={(e) => setHeliacal(e.target.checked)}
            />{" "}
            Jupiter by heliacal rising too
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
                  <span className="verse-rail-ref">xiv.{card.verses}</span>
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
                  prefix="xiv"
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
              Not laid out: v.3, which only lists what solar time governs; v.22-27, the closing
              narrative of the Sun&apos;s departure and Maya&apos;s instruction of the sages; and
              v.28-30, which are Burgess&apos;s appendix, not the text. The solar year is that of
              the date&apos;s Gregorian year, and the punyakala uses the Sun&apos;s mean disk.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
