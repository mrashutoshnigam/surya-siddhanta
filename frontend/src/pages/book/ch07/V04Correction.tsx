import { GridTable, KVTable } from "../../../components/Tables";
import { fmt } from "../ch01/scale";
import { fmtDate } from "../dates";
import type { CorrectionCard } from "./types";

/**
 * vii.4-6 — fixing the time of the conjunction.
 *
 * The gap in longitude, multiplied by sixty and divided by the difference of
 * the daily motions, gives nadis; it is subtracted when the conjunction is
 * past and added when it is to come (v.5). The longitudes are found again for
 * the new time and the step repeated until the two are equal (v.6). Each step
 * of that repetition is a row below.
 */
export function V04Correction({ card }: { card: CorrectionCard }) {
  return (
    <>
      <GridTable
        headers={["Step", "Gap", "Difference of motions", "Move", "Rule"]}
        rows={card.steps.map((s, i) => [
          i + 1,
          `${fmt(s.gap_arcmin)}′`,
          `${fmt(s.relative_speed)}°/day`,
          `${fmt(Math.abs(s.move_ghatis))} nadis`,
          s.rule === "add" ? "add" : "subtract",
        ])}
      />
      <KVTable
        rows={[
          [
            "Settled by the verse",
            card.final_date ? <strong>{fmtDate(card.final_date)}</strong> : "did not settle",
          ],
          [
            "Library (bisection)",
            card.library_date ? fmtDate(card.library_date) : "no conjunction within the window",
          ],
        ]}
      />
      {card.library_date && (
        <p className="ss-note">
          {card.agrees
            ? "The repetition and the library's bisection find the same moment."
            : "The repetition did not reach the library's conjunction: it started too far away and settled on a different crossing, or did not settle."}
        </p>
      )}
    </>
  );
}
