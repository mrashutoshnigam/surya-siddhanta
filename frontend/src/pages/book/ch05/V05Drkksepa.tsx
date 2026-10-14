import { KVTable } from "../../../components/Tables";
import { fmt } from "../ch01/scale";
import type { DrkksepaCard } from "./types";

/**
 * v.5-7 — the ecliptic zenith-distance (drkksepa) and ecliptic altitude (drggati).
 *
 * The verse takes the square root of the meridian-sine squared less
 * (meridian-sine × udaya) squared; that treats the spherical triangle as a
 * plane one, so it drifts from the library's exact nonagesimal as the
 * drkksepa grows. v.7 gives the cruder shortcut of taking the meridian
 * zenith-distance itself.
 */
export function V05Drkksepa({ card }: { card: DrkksepaCard }) {
  return (
    <>
      <KVTable
        rows={[
          ["Meridian zenith-distance", `${fmt(card.natamsa)}°`],
          ["Meridian-sine (madhyajya)", fmt(card.madhyajya)],
          ["Udaya", fmt(card.udaya)],
          ["Drkksepa by the verse (v.6)", <strong>{fmt(card.drkksepa_verse)}°</strong>],
          ["Drkksepa by the library (exact)", <strong>{fmt(Math.abs(card.drkksepa_library))}°</strong>],
          ["Difference", `${fmt(card.drkksepa_gap)}°`],
          ["Drggati (sine of ecliptic altitude)", fmt(card.drggati)],
          ["Approximation of v.7: drkksepa, drggati", `${fmt(card.approx_drkksepa)}°, ${fmt(card.approx_drggati)}`],
        ]}
      />
      <p className="ss-note">
        The library measures from the nonagesimal, which is exact; the verse uses a plane
        triangle. They agree closely near the equator and part company at high latitude.
      </p>
    </>
  );
}
