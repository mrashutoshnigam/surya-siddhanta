import { KVTable } from "../../../components/Tables";
import { fmt } from "../ch01/scale";
import type { SphereCard } from "./types";

/**
 * xii.42-44 — how the sphere turns at a latitude.
 *
 * The pole is raised above the horizon by the latitude. At no latitude the
 * asterisms pass overhead; at a pole they circle the horizon; between, day
 * and night depart from thirty nadis by the ascensional difference of
 * Chapter 3, which this card does not compute.
 */
export function V42Sphere({ card }: { card: SphereCard }) {
  return (
    <>
      <KVTable
        rows={[
          ["Latitude", `${fmt(card.latitude)}°`],
          ["Aspect of the sphere", <strong>{card.kind}</strong>],
          ["Pole above the horizon", `${fmt(card.pole_altitude)}°`],
          ["Co-latitude", `${fmt(card.colatitude)}°`],
          ["Hemisphere of", card.hemisphere],
          ["Day at this latitude", card.day_ghatis == null ? "depends on the Sun's declination" : `${fmt(card.day_ghatis)} ghatis`],
        ]}
      />
      <p className="ss-note">{card.description}</p>
    </>
  );
}
