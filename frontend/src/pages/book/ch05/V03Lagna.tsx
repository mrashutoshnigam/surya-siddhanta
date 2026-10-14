import { KVTable } from "../../../components/Tables";
import { dms, fmt } from "../ch01/scale";
import type { LagnaCard } from "./types";

/**
 * v.3-4 — the orient ecliptic-point and the meridian one.
 *
 * Udaya is the sine of the greatest declination times the sine of the
 * lagna's longitude, over the sine of the co-latitude (v.3). The meridian
 * zenith-distance is the place's latitude against the madhyalagna's
 * declination (v.4).
 */
export function V03Lagna({ card }: { card: LagnaCard }) {
  return (
    <KVTable
      rows={[
        ["Local sidereal time", dms(card.local_sidereal_time)],
        ["Orient ecliptic-point (lagna)", dms(card.lagna)],
        [
          "Udaya = sin ε × sin(lagna) ÷ cos(latitude)",
          <strong>{fmt(card.udaya)}</strong>,
        ],
        ["Meridian ecliptic-point (madhyalagna)", dms(card.madhyalagna)],
        ["Its declination", `${fmt(card.madhya_declination)}° ${card.direction}`],
        [
          `Meridian zenith-distance (|${fmt(card.latitude)}° − declination|)`,
          <strong>{fmt(card.natamsa)}°</strong>,
        ],
      ]}
    />
  );
}
