import { KVTable } from "../../../components/Tables";
import { fmt } from "../ch01/scale";
import type { VisibilityCard } from "./types";

/**
 * x.1 — when the Moon is seen.
 *
 * The Moon becomes visible in the west, or invisible in the east, at twelve
 * degrees of time from the Sun. The distance is taken on whichever side she
 * stands, so a waxing Moon is judged after sunset and a waning one before
 * sunrise. As in Chapter 9, the library reads the degrees on the ecliptic.
 */
export function V01Visibility({ card }: { card: VisibilityCard }) {
  return (
    <KVTable
      rows={[
        ["Elongation from the Sun", `${fmt(card.elongation)}°`],
        ["Distance from the Sun", `${fmt(card.distance)}°`],
        ["Limit of visibility", `${card.limit}°`],
        ["Seen in the", card.horizon],
        ["The Moon is", <strong>{card.visible ? "visible" : "lost in the Sun's rays"}</strong>],
      ]}
    />
  );
}
