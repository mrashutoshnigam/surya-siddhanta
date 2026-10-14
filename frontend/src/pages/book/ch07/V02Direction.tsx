import { KVTable } from "../../../components/Tables";
import { dms, fmt } from "../ch01/scale";
import type { DirectionCard } from "./types";

/**
 * vii.2-3 — is the conjunction past or to come.
 *
 * When the swifter planet's longitude is the greater the conjunction is past
 * (v.2); when one planet is retrograde the verse reads the other way round
 * (v.3). Both are one rule: the gap and the difference of the daily motions
 * have the same sign when the bodies are drawing apart.
 */
export function V02Direction({ card }: { card: DirectionCard }) {
  const motion = (m: number, retro: boolean) => `${fmt(m)}°/day${retro ? " (retrograde)" : ""}`;
  return (
    <KVTable
      rows={[
        [`${card.planet1}, longitude`, dms(card.longitude1)],
        [`${card.planet2}, longitude`, dms(card.longitude2)],
        [`${card.planet1} − ${card.planet2}`, `${fmt(card.gap)}°`],
        [`${card.planet1}, daily motion`, motion(card.motion1, card.retrograde1)],
        [`${card.planet2}, daily motion`, motion(card.motion2, card.retrograde2)],
        ["Swifter", card.swifter],
        ["Rule applied", card.rule === "v.3" ? "v.3 (one is retrograde)" : "v.2 (both direct)"],
        ["The conjunction is", <strong>{card.status}</strong>],
      ]}
    />
  );
}
