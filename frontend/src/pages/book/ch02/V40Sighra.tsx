import { useState } from "react";
import { KVTable } from "../../../components/Tables";
import { Picker } from "../../../components/VerseCard";
import { dms, fmt } from "../ch01/scale";
import type { SighraCard } from "./types";

/** Radius of the sine table, for showing the verse's phalas in its own units. */
const R = 3438;

/**
 * ii.40-42 — the equation of the conjunction.
 *
 * This is step 4 of the true place (ii.43-45): the anomaly is the sighrocca
 * less the place already corrected by the whole manda, so it is the sighra
 * anomaly of ii.29-30 and the phala is the last stage of ii.43-45.
 *
 * The koti-phala is added to the radius when the anomaly is in the half-orbit
 * beginning with Capricorn and subtracted in the half beginning with Cancer
 * (the shipped value is already signed); with the bhuja-phala it forms a
 * hypotenuse, and the sighra-phala is the arc whose sine is bhuja-phala ÷
 * hypotenuse.
 */
export function V40Sighra({ card }: { card: SighraCard }) {
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
      <p className="verse-note">
        {card.no_sighra.join(" and ")} have no conjunction correction, so they are not listed.
      </p>
      <KVTable
        rows={[
          ["Manda-corrected place (whole manda, step 3) · sighrocca", `${dms(r.manda_sphuta)} · ${dms(r.sighrocca)}`],
          ["Anomaly (kendra)", `${fmt(r.kendra)}° — quadrant ${r.quadrant}`],
          ["Epicycle at this anomaly", `${fmt(r.epicycle)}°`],
          ["Koti-phala (+ added to, − taken from the radius)", fmt(r.kotiphala * R)],
          ["Bhuja-phala", fmt(r.bhujaphala * R)],
          ["Hypotenuse", fmt(r.hypotenuse * R)],
          [
            "Equation of the conjunction",
            <strong>
              {r.phala >= 0 ? "+" : "−"}
              {dms(Math.abs(r.phala))}
            </strong>,
          ],
        ]}
      />
    </>
  );
}
