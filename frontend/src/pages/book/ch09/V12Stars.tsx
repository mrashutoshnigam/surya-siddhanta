import { GridTable } from "../../../components/Tables";
import type { StarsCard } from "./types";

/**
 * ix.12-18 — the fixed stars.
 *
 * The stars too are hidden by the Sun, each within its own distance in
 * degrees of time; the figures are the verses' and nothing is computed from
 * them. The stars of northern situation are never extinguished (v.18).
 */
export function V12Stars({ card }: { card: StarsCard }) {
  return (
    <>
      <GridTable
        headers={["Limit", "Verse", "Stars"]}
        rows={card.groups.map((g) => [`${g.degrees}°`, `ix.${g.verse}`, g.stars.join(", ")])}
      />
      <p className="ss-note">
        Never extinguished by the Sun's rays (v.18): {card.circumpolar.join(", ")}.
      </p>
    </>
  );
}
