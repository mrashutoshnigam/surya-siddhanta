import { GridTable, KVTable } from "../../../components/Tables";
import { fmt } from "../ch01/scale";
import type { JovianYear, JupiterCard } from "./types";

function yearRows(y: JovianYear): [string, string][] {
  return [
    ["Year of the cycle", `${y.name} (${y.asterism}, ${fmt(y.longitude)}°)`],
    ["Jovian years since the epoch", String(y.jovian_years_elapsed)],
    ["Sixty-year name (Ch.1 i.55, a separate cycle)", y.sixty_year_name],
  ];
}

/**
 * xiv.17 — Jupiter's years.
 *
 * The mean method follows Jupiter's mean place through the month-and-asterism
 * table (Burgess's reading). The text's own rule names the year from his
 * heliacal rising; that reconstruction rests on Chapter 9's visibility limits
 * and is shown only on request, with a note where the two disagree. Both are
 * marked as commentary. The
 * cycle steps in exact Jovian years (30° of his mean motion): a name spans
 * two or three asterisms, so it advances by 0, 1 or 2 places a step.
 */
export function V17Jupiter({ card }: { card: JupiterCard }) {
  return (
    <>
      <KVTable title="Mean method (commentary)" rows={yearRows(card.mean)} />
      {card.heliacal && (
        <>
          <KVTable title="Heliacal method (commentary)" rows={yearRows(card.heliacal)} />
          {card.heliacal.note && <p className="ss-note">{card.heliacal.note}</p>}
        </>
      )}
      <div className="table-scroll">
        <GridTable
          headers={["Jovian year", "Name", "Asterism", "Advance"]}
          rows={card.cycle.map((y, i) => [i + 1, y.name, y.asterism, y.advance])}
        />
      </div>
    </>
  );
}
