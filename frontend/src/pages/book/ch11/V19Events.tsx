import { GridTable } from "../../../components/Tables";
import { fmt } from "../ch01/scale";
import { fmtDate } from "../dates";
import type { EventsCard } from "./types";

/**
 * xi.19 — twice, or not at all.
 *
 * Near the equator the declination condition can be met twice around one
 * longitude-sum crossing, giving a pata a second occurrence; elsewhere it
 * can fail to be met at all, and the crossing passes with no true pata. The
 * library marks a pata whose declination condition never resolved inside
 * its search window as unrefined, rather than guessing.
 */
export function V19Events({ card }: { card: EventsCard }) {
  if (card.events.length === 0) {
    return <p className="ss-note">No pata falls within the {card.days}-day window.</p>;
  }
  return (
    <>
      <div className="table-scroll">
        <GridTable
          headers={["Kind", "True instant", "Duration (ghatis)", "Refined"]}
          rows={card.events.map((e) => [
            e.kind,
            fmtDate(e.middle),
            fmt(e.duration_ghatis),
            e.refined ? "yes" : "no — crossing kept as nominal",
          ])}
        />
      </div>
      {card.unrefined_count > 0 && (
        <p className="ss-note">
          {card.unrefined_count} of {card.events.length} pata
          {card.unrefined_count === 1 ? "" : "s"} in this window never saw the declinations
          actually equalize — the nominal longitude-sum crossing is kept instead (v.19's
          near-equator case).
        </p>
      )}
    </>
  );
}
