import { KVTable } from "../../../components/Tables";
import { dms, fmt } from "../ch01/scale";
import type { NoParallaxCard } from "./types";

/**
 * v.1 — where there is no parallax.
 *
 * Longitude parallax vanishes when the Sun is at the meridian ecliptic-point;
 * latitude parallax vanishes when the place's latitude equals that point's
 * northern declination. The card shows how far this new moon is from each.
 */
export function V01NoParallax({ card }: { card: NoParallaxCard }) {
  return (
    <KVTable
      rows={[
        ["Latitude of the place", `${fmt(card.latitude)}°`],
        ["Sun (sayana)", dms(card.sun)],
        ["Meridian ecliptic-point (madhyalagna)", dms(card.madhyalagna)],
        [
          "Sun − madhyalagna",
          <>
            <strong>{fmt(card.interval)}°</strong>
            {card.lambana_vanishes ? " — no parallax in longitude" : ""}
          </>,
        ],
        ["Declination of the madhyalagna", `${fmt(card.madhya_declination)}°`],
        [
          "Latitude − that declination",
          <>
            <strong>{fmt(card.latitude_gap)}°</strong>
            {card.nati_vanishes ? " — no parallax in latitude" : ""}
          </>,
        ],
      ]}
    />
  );
}
