import { KVTable } from "../../../components/Tables";
import { fmt } from "../ch01/scale";
import type { CirclesCard } from "./types";

/**
 * vi.2 — the circles of the figure.
 *
 * A deflection circle of 49 digits, then the aggregate circle whose radius
 * is half the sum of the eclipsed and eclipsing bodies. The verses lay
 * minutes off as digits, so the radii below are both.
 */
export function V02Circles({ card }: { card: CirclesCard }) {
  return (
    <KVTable
      rows={[
        ["Deflection circle (valana)", `${fmt(card.valana_circle)} digits`],
        [`Eclipsed: ${card.eclipsed_body}, radius`, `${fmt(card.eclipsed_radius)}′`],
        [`Eclipsing: ${card.eclipser_body}, radius`, `${fmt(card.eclipser_radius)}′`],
        ["Aggregate circle (half the sum)", <strong>{fmt(card.aggregate_radius)}′</strong>],
        ["Half the difference", `${fmt(card.half_difference)}′`],
      ]}
    />
  );
}
