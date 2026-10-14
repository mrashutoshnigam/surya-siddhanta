import { GridTable } from "../../../components/Tables";
import { fmt } from "../ch01/scale";
import { fmtDate } from "../dates";
import type { EventsCard } from "./types";

/**
 * ix.6-11 — every rising and setting in the months ahead.
 *
 * The library scans day by day for the elongation crossing the limit and
 * bisects each crossing. A rising is where the planet becomes visible after
 * its conjunction, a setting where it is swallowed by the Sun's rays.
 */
export function V06Events({ card }: { card: EventsCard }) {
  if (card.events.length === 0) {
    return <p className="ss-note">{card.planet} has no heliacal event in the window.</p>;
  }
  return (
    <div className="table-scroll">
      <GridTable
        headers={["Event", "Date", "Elongation", "In the"]}
        rows={card.events.map((e) => [e.type, fmtDate(e.date), `${fmt(e.elongation)}°`, e.direction])}
      />
    </div>
  );
}
