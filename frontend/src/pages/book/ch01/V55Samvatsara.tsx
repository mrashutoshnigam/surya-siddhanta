import { useState } from "react";
import { KVTable } from "../../../components/Tables";
import { Slider } from "../../../components/VerseCard";
import { fmt, grouped } from "./scale";
import type { SamvatsaraCard } from "./types";

/**
 * i.55 — the current year of Jupiter's sixty-year cycle.
 *
 * v.55 takes Jupiter's past revolutions, multiplies by twelve, adds the
 * signs of the current revolution and divides by sixty, counting the
 * remainder from Vijaya. The slider drags the ahargana through that, so
 * the cycle can be watched turning a name at a time.
 */
export function V55Samvatsara({ card }: { card: SamvatsaraCard }) {
  const [ahargana, setAhargana] = useState(Math.round(card.ahargana));

  const revolutions = (card.jupiter_bhagana * ahargana) / card.civil_days_per_mahayuga;
  const jovianYears = Math.floor(revolutions * 12);
  const index = ((jovianYears + card.vijaya_index) % 60 + 60) % 60;
  const previous = card.names[(index + 59) % 60];
  const next = card.names[(index + 1) % 60];

  return (
    <>
      <Slider
        label="Ahargana"
        value={ahargana}
        min={0}
        max={Math.round(card.ahargana) + 7305}
        step={1}
        suffix="days"
        onChange={setAhargana}
      />
      <p className="verse-readout">
        <strong>{card.names[index]}</strong> — year {index + 1} of the cycle
      </p>

      <KVTable
        rows={[
          ["Jupiter's revolutions", fmt(revolutions)],
          ["× 12, with the signs run", grouped(jovianYears)],
          ["counted from", `${card.counted_from} (year ${card.vijaya_index + 1})`],
          ["the year before", previous],
          ["the year after", next],
        ]}
      />
      <p className="verse-note">{card.note}</p>
    </>
  );
}
