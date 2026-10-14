import { KVTable } from "../../../components/Tables";
import { dms, fmt } from "../ch01/scale";
import type { OppositionCard } from "./types";

/** iv.7-8 — the full moon nearest the date: the Sun and Moon opposite, and the node. */
export function V07Opposition({ card }: { card: OppositionCard }) {
  return (
    <KVTable
      rows={[
        ["Day of the month", fmt(card.day)],
        ["Sun", dms(card.sun)],
        ["Moon", `${card.moon_rashi} — ${dms(card.moon)}`],
        ["Moon − Sun", <strong>{dms(card.elongation)}</strong>],
        ["Node", dms(card.node)],
        ["Moon − node", dms(card.moon_minus_node)],
      ]}
    />
  );
}
