import { KVTable } from "../../../components/Tables";
import type { WhoCard } from "./types";

/**
 * vii.1 — who meets whom.
 *
 * Only the five star-planets can be in encounter (yuddha) or conjunction
 * (samagama) with one another; with the Moon there is conjunction only, and a
 * planet near the Sun is lost in his light.
 */
export function V01Who({ card }: { card: WhoCard }) {
  const yes = (b: boolean) => (b ? "a star-planet (tara-graha)" : "not a star-planet");
  return (
    <KVTable
      rows={[
        [card.planet1, yes(card.planet1_taragraha)],
        [card.planet2, yes(card.planet2_taragraha)],
        ["This pair", <strong>{card.relation}</strong>],
      ]}
    />
  );
}
