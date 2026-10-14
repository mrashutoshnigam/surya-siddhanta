import { KVTable } from "../../../components/Tables";
import { fmt } from "../ch01/scale";
import type { SinesCard } from "./types";

/**
 * xiii.14-15 — the sines and the raised pole.
 *
 * In the text's R = 3438 units. Verse 14 describes the day-measure (antya) in
 * the Sun's small circle; the treatise's own antya is the great-circle figure
 * R + carajya. Burgess calls the verse a blunder, so both are shown. The pole
 * stands above the horizon by the latitude.
 */
export function V14Sines({ card }: { card: SinesCard }) {
  const s = card.sines;
  return (
    <KVTable
      rows={[
        ["Sun's declination", `${fmt(card.sun_declination)}°`],
        ["Sine of declination (krantijya)", fmt(s.krantijya)],
        ["Day-radius (dyujya)", fmt(s.dyujya)],
        ["Earth-sine (kujya)", fmt(s.kujya)],
        ["Sine of ascensional difference (carajya)", fmt(s.carajya)],
        ["Day-measure, great circle (the treatise's antya)", fmt(s.antya_great_circle)],
        ["Day-measure, small circle (as v.14 words it)", fmt(s.antya_small_circle)],
        ["Pole above the horizon", `${fmt(card.pole_altitude)}°`],
      ]}
    />
  );
}
