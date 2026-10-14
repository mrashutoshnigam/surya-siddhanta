import { KVTable } from "../../../components/Tables";
import { fmt } from "../ch01/scale";
import type { VisibilityCard } from "./types";

/**
 * vi.13 — what can be seen.
 *
 * The Moon's clearness shows an eclipse down to a twelfth of her disk;
 * the Sun's brilliancy hides even three minutes of his.
 */
export function V13Visibility({ card }: { card: VisibilityCard }) {
  const lunar = card.kind === "lunar";
  return (
    <KVTable
      rows={[
        [
          lunar ? "Least seen: a twelfth of the Moon" : "Least seen: three minutes of the Sun",
          `${fmt(card.threshold)}′`,
        ],
        ["This eclipse obscures", card.is_eclipse ? `${fmt(card.obscured)}′` : "nothing"],
        [
          "Observable?",
          <strong>{card.is_eclipse ? (card.visible ? "yes" : "no — too small to be seen") : "no eclipse"}</strong>,
        ],
      ]}
    />
  );
}
