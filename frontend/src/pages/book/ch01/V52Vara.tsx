import { useState } from "react";
import { GridTable } from "../../../components/Tables";
import { Slider } from "../../../components/VerseCard";
import type { VaraCard } from "./types";

/**
 * i.52 — the lord of the day.
 *
 * The weekday is the ahargana counted round seven, so a slider of days is
 * the whole of the interaction: move it and the lordship moves with it.
 */
export function V52Vara({ card }: { card: VaraCard }) {
  const [offsetDays, setOffsetDays] = useState(0);

  const index = ((card.number + offsetDays) % 7 + 7) % 7;
  const current = card.order[index];

  return (
    <>
      <Slider
        label="Days from this date"
        value={offsetDays}
        min={-14}
        max={14}
        step={1}
        suffix="days"
        onChange={setOffsetDays}
      />
      <p className="verse-readout">
        <strong>{current.name}</strong> — {current.name_en}
        {offsetDays === 0 ? "" : `, ${Math.abs(offsetDays)} days ${offsetDays > 0 ? "on" : "back"}`}
      </p>

      <GridTable
        headers={["#", "Vara", "Weekday"]}
        rows={card.order.map((v) => [
          v.number,
          <span className={v.number === index ? "unit-selected" : undefined}>{v.name}</span>,
          v.name_en,
        ])}
      />
    </>
  );
}
