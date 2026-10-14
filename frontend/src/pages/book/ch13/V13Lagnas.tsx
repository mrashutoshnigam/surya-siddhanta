import { GridTable, KVTable } from "../../../components/Tables";
import { fmt } from "../ch01/scale";
import type { LagnasCard } from "./types";

/**
 * xiii.13-14 — the three lagnas.
 *
 * Computed exactly on the horizon: the orient point is the ecliptic point
 * actually rising, not Chapter 3's lagna (which is uncorrected). Tropical
 * longitude fixes the point on the sphere; sidereal is the frame the rest of
 * the treatise reckons in.
 */
export function V13Lagnas({ card }: { card: LagnasCard }) {
  return (
    <>
      <KVTable
        rows={[
          ["Local sidereal time", `${fmt(card.lst_deg)}°`],
          ["Ayanamsha", `${fmt(card.ayanamsha)}°`],
        ]}
      />
      <div className="table-scroll">
        <GridTable
          headers={["Point", "Tropical", "Sidereal", "Right ascension", "Declination"]}
          rows={card.points.map((p) => [
            p.name,
            `${fmt(p.tropical_longitude)}°`,
            `${fmt(p.sidereal_longitude)}°`,
            `${fmt(p.right_ascension)}°`,
            `${fmt(p.declination)}°`,
          ])}
        />
      </div>
    </>
  );
}
