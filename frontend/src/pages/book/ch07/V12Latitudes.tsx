import { KVTable } from "../../../components/Tables";
import { fmt } from "../ch01/scale";
import { fmtDate } from "../dates";
import type { LatitudesCard } from "./types";

/** North/south word for a signed latitude in arcminutes. */
function lat(value: number): string {
  return `${fmt(Math.abs(value))}′ ${value >= 0 ? "north" : "south"}`;
}

/**
 * vii.12 — the latitudes at the conjunction.
 *
 * The longitudes and latitudes are found again for the fixed time. When the
 * two latitudes lie the same way the difference is taken, otherwise the sum:
 * the distance between the bodies across the ecliptic.
 */
export function V12Latitudes({ card, one, two }: { card: LatitudesCard; one: string; two: string }) {
  if (!card.found) {
    return <p className="ss-note">There is no conjunction of this pair within the search window.</p>;
  }
  return (
    <KVTable
      rows={[
        ["Conjunction", fmtDate(card.date)],
        [`${one}, latitude`, lat(card.latitude1)],
        [`${two}, latitude`, lat(card.latitude2)],
        ["The latitudes lie", card.same_direction ? "the same way — take the difference" : "opposite ways — take the sum"],
        ["Distance across the ecliptic", <strong>{fmt(card.verse_gap)}′</strong>],
        ["Library (great-circle separation)", `${fmt(card.library_separation_arcmin)}′`],
      ]}
    />
  );
}
