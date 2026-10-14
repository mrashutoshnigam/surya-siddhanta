import { useState } from "react";
import { GridTable } from "../../../components/Tables";
import { Picker } from "../../../components/VerseCard";
import { dms } from "../ch01/scale";
import type { TruePlaceCard } from "./types";

/**
 * ii.43-45 — the true place, in the text's four steps.
 *
 * Half the sighra, half the manda, the whole manda on the mean place, then
 * the whole sighra. The Sun and Moon need only the manda (v.43).
 */
export function V43TruePlace({ card }: { card: TruePlaceCard }) {
  const [body, setBody] = useState(card.rows[0].body);
  const r = card.rows.find((x) => x.body === body) ?? card.rows[0];

  return (
    <>
      <Picker
        label="Body"
        value={body}
        options={card.rows.map((x) => ({ value: x.body, label: x.body }))}
        onChange={setBody}
      />
      <GridTable
        headers={["Step", "Correction", "Longitude"]}
        rows={r.stages.map((s, i) => [
          s.label,
          s.correction === null ? "—" : `${s.correction >= 0 ? "+" : "−"}${dms(Math.abs(s.correction))}`,
          <span className={i === r.stages.length - 1 ? "unit-selected" : undefined}>{dms(s.longitude)}</span>,
        ])}
      />
      <p className="verse-readout">
        True longitude <strong>{dms(r.true_longitude)}</strong> — {r.rashi}
      </p>
      {r.stages.length === 2 && (
        <p className="verse-note">The Sun and Moon need only the equation of the apsis.</p>
      )}
    </>
  );
}
