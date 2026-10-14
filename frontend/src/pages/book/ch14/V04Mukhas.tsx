import { GridTable } from "../../../components/Tables";
import { fmt } from "../ch01/scale";
import { fmtDate } from "../dates";
import type { MukhasCard } from "./types";

/**
 * xiv.4-6 — the shadasitimukhas.
 *
 * Four points 86 degrees apart from Libra, leaving sixteen degrees at the end
 * of Virgo. The text's "eighty-six days" are degrees: the arcs are equal but
 * the Sun's motion is not, so the days between them are not.
 */
export function V04Mukhas({ card }: { card: MukhasCard }) {
  return (
    <>
      <div className="table-scroll">
        <GridTable
          headers={["Point", "Longitude", "Arc", "Reached", "Days over the arc"]}
          rows={card.marks.map((m) => [
            m.name,
            `${fmt(m.longitude)}°`,
            `${fmt(m.arc_degrees)}°`,
            fmtDate(m.date),
            fmt(m.measured_days),
          ])}
        />
      </div>
      <p className="ss-note">{card.note}</p>
      {card.marks[4]?.use && <p className="ss-note">{card.marks[4].use}</p>}
    </>
  );
}
