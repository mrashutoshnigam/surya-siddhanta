import { GridTable, KVTable } from "../../../components/Tables";
import { dms, fmt } from "../ch01/scale";
import { fmtDate } from "../dates";
import type { ConjunctionsCard } from "./types";

/**
 * viii.14-15 — a planet meets a star.
 *
 * The chapter ends by sending the reader back to Chapter 7: calculate the
 * conjunction of a planet and an asterism by the same method, with the star
 * held at its catalog longitude. The library scans daily and bisects each
 * crossing; a retrograde planet may cross more than once.
 */
export function V14Conjunctions({ card }: { card: ConjunctionsCard }) {
  return (
    <>
      <KVTable
        rows={[
          [`${card.star}, longitude and latitude`, `${dms(card.star_longitude)}, ${fmt(card.star_latitude)}°`],
          ["Searched", `${card.months} months from 1 January ${card.year}`],
        ]}
      />
      {card.conjunctions.length === 0 ? (
        <p className="ss-note">{card.planet} does not reach this star's longitude in that time.</p>
      ) : (
        <GridTable
          headers={["Conjunction", "Interval (latitude of star)"]}
          rows={card.conjunctions.map((c) => [fmtDate(c.date), `${fmt(c.separation_deg)}°`])}
        />
      )}
    </>
  );
}
