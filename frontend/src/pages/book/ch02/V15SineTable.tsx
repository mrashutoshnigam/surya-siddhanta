import { GridTable } from "../../../components/Tables";
import { grouped } from "../ch01/scale";
import type { SineTableCard } from "./types";

/**
 * ii.15-27 — the table of sines and of versed sines.
 *
 * Fixed: twenty-four tabular sines of a quadrant in steps of 3°45′, with
 * the first difference of each and the error against a modern sine.
 */
export function V15SineTable({ card }: { card: SineTableCard }) {
  return (
    <>
      <p className="verse-readout">
        Radius <strong>{grouped(card.radius)}′</strong>. First sine: a sign&apos;s{" "}
        {grouped(card.sign_arcmin)}′ ÷ 8 = <strong>{card.first_sine}′</strong>, which is also the
        step of the table ({card.step_arcmin}′).
      </p>
      <GridTable
        headers={["#", "Arc", "Sine (jya)", "First difference", "Versed sine", "Modern R·sin", "Error"]}
        rows={card.rows.map((r) => [
          r.index,
          `${r.degrees}° (${grouped(r.arcmin)}′)`,
          grouped(r.jya),
          grouped(r.difference),
          grouped(r.utkrama),
          r.modern.toFixed(2),
          r.error.toFixed(2),
        ])}
      />
      <p className="verse-note">{card.note}</p>
    </>
  );
}
