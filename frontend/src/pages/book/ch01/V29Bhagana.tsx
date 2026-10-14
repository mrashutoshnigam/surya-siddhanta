import { useState } from "react";
import { GridTable } from "../../../components/Tables";
import { Picker, Slider } from "../../../components/VerseCard";
import { fmt, grouped } from "./scale";
import type { BhaganaCard } from "./types";

/**
 * i.29-34 — the revolutions in an Age, and what they come to in a span.
 *
 * Pick a body and drag a number of days: the card states the revolutions
 * that body completes in them, which is the v.35 proportion before it is
 * reduced to a longitude.
 */
export function V29Bhagana({ card }: { card: BhaganaCard }) {
  const [body, setBody] = useState(card.rows[0].body);
  const [days, setDays] = useState(365);

  const selected = card.rows.find((r) => r.body === body) ?? card.rows[0];
  const revolutions = (selected.revolutions * days) / card.civil_days_per_mahayuga;

  return (
    <>
      <Picker
        label="Body"
        value={body}
        options={card.rows.map((r) => ({ value: r.body, label: r.body.replace("_", " ") }))}
        onChange={setBody}
      />
      <Slider
        label="Days elapsed"
        value={days}
        min={1}
        max={36525}
        step={1}
        suffix="days"
        onChange={setDays}
      />
      <p className="verse-readout">
        In {grouped(days)} days {selected.body.replace("_", " ")} completes{" "}
        <strong>{fmt(revolutions)}</strong> revolutions — {fmt(revolutions * 360)}° of motion.
      </p>

      <GridTable
        headers={[
          "Body",
          "Revolutions in an Age",
          "Daily motion",
          "Arcmin / day",
          "One revolution",
        ]}
        rows={card.rows.map((r) => [
          <span className={r.body === selected.body ? "unit-selected" : undefined}>
            {r.body.replace("_", " ")}
          </span>,
          grouped(r.revolutions),
          `${fmt(r.daily_motion_deg)}°`,
          fmt(r.daily_motion_arcmin),
          `${fmt(r.period_days)} days`,
        ])}
      />
      <p className="verse-note">{card.note}</p>
    </>
  );
}
