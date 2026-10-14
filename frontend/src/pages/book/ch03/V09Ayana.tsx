import { GridTable, KVTable } from "../../../components/Tables";
import { dms, fmt } from "../ch01/scale";
import type { AyanaCard } from "./types";

/** iii.9-12 — the precession offset, and its effect on each body's longitude. */
export function V09Ayana({ card }: { card: AyanaCard }) {
  return (
    <>
      <KVTable
        rows={[
          ["Ayanamsha", <strong>{dms(card.ayanamsha)}</strong>],
          ["Years since the Kali epoch", fmt(card.kali_years)],
          ["Period of the oscillation", `${fmt(card.period_years)} years`],
        ]}
      />
      <GridTable
        headers={["Body", "Sidereal", "Tropical (sidereal + ayanamsha)"]}
        rows={card.rows.map((r) => [r.body, `${r.rashi} — ${dms(r.sidereal)}`, dms(r.tropical)])}
      />
    </>
  );
}
