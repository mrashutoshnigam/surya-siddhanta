import { GridTable, KVTable } from "../../../components/Tables";
import { fmt } from "../ch01/scale";
import type { PointsCard } from "./types";

/**
 * xiii.10-11 — equinoxes, solstices and the signs.
 *
 * The sphere's own longitudes: signs are counted from the equinox, so no
 * ayanamsha applies. The chord of thirty degrees (in the text's R = 3438) is
 * what lays the twelve divisions off on the ecliptic hoop.
 */
export function V10Points({ card }: { card: PointsCard }) {
  return (
    <>
      <div className="table-scroll">
        <GridTable
          headers={["Point", "Longitude", "Right ascension", "Declination"]}
          rows={card.cardinal.map((p) => [
            p.name,
            `${fmt(p.tropical_longitude)}°`,
            `${fmt(p.right_ascension)}°`,
            `${fmt(p.declination)}°`,
          ])}
        />
      </div>
      <div className="table-scroll">
        <GridTable
          headers={["Sign", "Longitude", "Right ascension", "Declination"]}
          rows={card.signs.map((p) => [
            p.name,
            `${fmt(p.tropical_longitude)}°`,
            `${fmt(p.right_ascension)}°`,
            `${fmt(p.declination)}°`,
          ])}
        />
      </div>
      <KVTable rows={[["Chord of 30° (R = 3438)", fmt(card.chord_of_thirty)]]} />
    </>
  );
}
