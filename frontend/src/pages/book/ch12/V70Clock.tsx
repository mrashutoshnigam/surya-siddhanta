import { GridTable } from "../../../components/Tables";
import { fmt } from "../ch01/scale";
import type { ClockCard } from "./types";

/**
 * xii.70-71 — the cities' clock.
 *
 * The four cities lie on the equator a quadrant apart, so each is six hours
 * from the next. Given noon at Ujjayini, the other hours follow from the
 * difference of longitude alone.
 */
export function V70Clock({ card }: { card: ClockCard }) {
  return (
    <>
      <p className="ss-note">
        When it is {fmt(card.anchor_hour)}:00 at {card.anchor}, the local hour elsewhere is:
      </p>
      <div className="table-scroll">
        <GridTable
          headers={["Place", "Longitude", "Local hour"]}
          rows={card.hours.map((h) => [
            h.name === card.anchor ? <strong key={h.name}>{h.name}</strong> : h.name,
            `${fmt(h.longitude)}°`,
            `${fmt(h.hour)}:00`,
          ])}
        />
      </div>
    </>
  );
}
