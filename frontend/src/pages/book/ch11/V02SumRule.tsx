import { KVTable } from "../../../components/Tables";
import { fmt } from "../ch01/scale";
import type { SumRuleCard } from "./types";

/**
 * xi.2-3 — the longitude-sum rule.
 *
 * Vyatipata falls where the Sun's and Moon's tropical longitudes sum to 180
 * degrees, Vaidhrita where they sum to 360. The sum is only the trigger —
 * which of the two the sum is heading for next, by itself, says nothing
 * about the declination condition the later verses add.
 */
export function V02SumRule({ card }: { card: SumRuleCard }) {
  return (
    <KVTable
      rows={[
        ["Longitude sum (Sun + Moon)", `${fmt(card.longitude_sum)}°`],
        ["Distance to Vyatipata (180°)", `${fmt(card.degrees_to_vyatipata)}°`],
        ["Distance to Vaidhrita (360°)", `${fmt(card.degrees_to_vaidhrita)}°`],
        ["Next by the sum rule", <strong>{card.next_by_sum_rule}</strong>],
      ]}
    />
  );
}
