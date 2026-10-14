import { useState } from "react";
import { KVTable } from "../../../components/Tables";
import { Picker } from "../../../components/VerseCard";
import { dms, fmt } from "../ch01/scale";
import type { MandaCard } from "./types";

/** ii.39 — the equation of the apsis for one body, applied once to its mean place. */
export function V39Manda({ card }: { card: MandaCard }) {
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
      <KVTable
        rows={[
          ["Mean place · apsis", `${dms(r.mean)} · ${dms(r.mandocca)}`],
          ["Anomaly (kendra)", `${fmt(r.kendra)}° — quadrant ${r.quadrant} (${r.odd ? "odd" : "even"})`],
          ["Bhuja · jya", `${fmt(r.bhuja)}° · ${fmt(r.bhuja_jya)}`],
          ["Epicycle at this anomaly", `${fmt(r.epicycle)}°`],
          [
            "Equation of the apsis",
            <strong>
              {r.phala >= 0 ? "+" : "−"}
              {dms(Math.abs(r.phala))}
            </strong>,
          ],
          ["Corrected place", `${dms(r.corrected)} — ${r.corrected_rashi}`],
        ]}
      />
      <p className="verse-note">
        Shown here applied once, whole, to the mean place, as the true place does for the Sun and Moon. For the star-planets the true place (ii.43-45) applies half of it first, then the whole on the mean place.
      </p>
    </>
  );
}
