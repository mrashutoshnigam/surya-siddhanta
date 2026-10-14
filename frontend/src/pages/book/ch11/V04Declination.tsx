import { KVTable } from "../../../components/Tables";
import { fmt } from "../ch01/scale";
import type { DeclinationCard } from "./types";

/**
 * xi.4-11 — the Moon's declination, corrected by her latitude.
 *
 * The correction is resolved along the declination circle through the ayana
 * valana, the angle between ecliptic and equator at the Moon's longitude.
 * v.7-8's gata/eshya rule — whether the nearest pata is already past or still
 * to come — follows from comparing the corrected declinations; here it is
 * read straight off the nearest event the search already found.
 */
export function V04Declination({ card }: { card: DeclinationCard }) {
  return (
    <>
      <KVTable
        rows={[
          ["Sun's declination", `${fmt(card.sun_declination)}°`],
          ["Moon's declination, corrected", `${fmt(card.moon_declination)}°`],
          ["Moon's declination, plain longitude", `${fmt(card.moon_declination_plain)}°`],
          ["Moon's latitude", `${fmt(card.moon_latitude_arcmin)}′`],
          ["Ayana valana", `${fmt(card.ayana_valana)}°`],
        ]}
      />
      {card.nearest_kind && (
        <p className="ss-note">
          The nearest pata ({card.nearest_kind}) is{" "}
          <strong>{card.is_past ? "already past" : "still to come"}</strong>.
        </p>
      )}
    </>
  );
}
