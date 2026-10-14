import { GridTable, KVTable } from "../../../components/Tables";
import { fmt } from "../ch01/scale";
import type { HoopsCard } from "./types";

const GROUPS: Record<string, string> = {
  junction_stars: "Junction stars of the asterisms (v.8)",
  fixed_stars: "Seven other fixed stars (v.9)",
};

/**
 * xiii.4-9 — the hoops of the sphere.
 *
 * The great hoops (equator, ecliptic, the two colures), the Sun's six diurnal
 * hoops at the sign boundaries 30°, 60° and 90° either side of the equinox,
 * and a diurnal hoop for each star. The 3D sphere is on the Instruments page.
 */
export function V04Hoops({ card }: { card: HoopsCard }) {
  return (
    <>
      <div className="table-scroll">
        <GridTable
          headers={["Great hoop", "Verse"]}
          rows={card.great.map((h) => [h.name, h.verse.replace("SS.", "")])}
        />
      </div>
      <div className="table-scroll">
        <GridTable
          headers={["Sun's hoop", "Declination", "Day-radius (dyujya)"]}
          rows={card.solar.map((h) => [h.name, `${fmt(h.declination)}°`, fmt(h.day_radius)])}
        />
      </div>
      <KVTable
        title="Stellar hoops"
        rows={Object.entries(card.stars).map(([group, n]) => [GROUPS[group] ?? group, n])}
      />
    </>
  );
}
