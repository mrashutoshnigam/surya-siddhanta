import { KVTable } from "../../../components/Tables";
import { dms, fmt } from "../ch01/scale";
import type { YogaCard } from "./types";

/** ii.65 — the yoga: the Sun's and Moon's longitudes added, divided by 13°20′. */
export function V65Yoga({ card }: { card: YogaCard }) {
  return (
    <KVTable
      rows={[
        ["Sun · Moon", `${dms(card.sun)} · ${dms(card.moon)}`],
        ["Sum", `${dms(card.sum)} = ${fmt(card.sum_arcmin)}′`],
        ["÷ 13°20′ (800′)", `yoga ${card.number} of 27`],
        ["Name", <strong>{card.name}</strong>],
        ["Elapsed", `${fmt(card.fraction * 100)}%`],
      ]}
    />
  );
}
