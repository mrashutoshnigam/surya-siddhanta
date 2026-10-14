import { KVTable } from "../../../components/Tables";
import { fmt } from "../ch01/scale";
import { fmtDate } from "../dates";
import type { TimingCard } from "./types";

/**
 * xi.12-14 — the true instant, and its duration.
 *
 * The true pata falls where the corrected declinations are equal, not where
 * the longitude sum alone crosses its target. Half-duration is the combined
 * semi-diameters of Sun and Moon over the difference of their daily
 * motions, as v.14 states.
 */
export function V12Timing({ card }: { card: TimingCard }) {
  if (!card.found || card.middle == null) {
    return <p className="ss-note">No pata falls within the search window.</p>;
  }
  return (
    <KVTable
      rows={[
        ["Kind", <strong>{card.kind}</strong>],
        ["Begins", fmtDate(card.begin!)],
        ["True instant", fmtDate(card.middle)],
        ["Ends", fmtDate(card.end!)],
        ["Duration", `${fmt(card.duration_ghatis!)} ghatis (${fmt(card.duration_hours!)} hours)`],
        ["Sun's declination at the instant", `${fmt(card.sun_declination!)}°`],
        ["Moon's declination at the instant", `${fmt(card.moon_declination!)}°`],
      ]}
    />
  );
}
