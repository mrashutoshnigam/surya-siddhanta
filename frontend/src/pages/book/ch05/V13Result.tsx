import { KVTable } from "../../../components/Tables";
import { fmt } from "../ch01/scale";
import type { ResultCard } from "./types";

/**
 * v.13 — the eclipse as seen from the place.
 *
 * With both parallaxes applied the half-duration, the amount obscured and the
 * type are recomputed as in a lunar eclipse. Beside it, the same new moon with
 * no parallax: the Moon's latitude alone often decides differently.
 */
export function V13Result({ card }: { card: ResultCard }) {
  return (
    <>
      <KVTable
        rows={[
          ["Day of the month", fmt(card.day)],
          ["Moon's diameter, Sun's diameter", `${fmt(card.moon_diameter)}′, ${fmt(card.sun_diameter)}′`],
          ["Lambana, nati", `${fmt(card.lambana ?? 0)}′, ${fmt(card.nati ?? 0)}′`],
          [
            "From this place",
            <strong>
              {card.is_eclipse
                ? `${card.eclipse_type}, ${fmt(card.magnitude)} obscured`
                : "no eclipse"}
            </strong>,
          ],
          ["Half-duration", card.is_eclipse && card.half_duration_min != null ? `${fmt(card.half_duration_min)} min` : "—"],
          ["Sun's altitude at conjunction", card.sun_altitude_deg != null ? `${fmt(card.sun_altitude_deg)}°` : "—"],
          [
            "With no parallax (geocentric)",
            `${card.geocentric_type}${card.geocentric_type === "none" ? "" : `, ${fmt(card.geocentric_magnitude)}`} — Moon's latitude ${fmt(card.geocentric_latitude)}′`,
          ],
        ]}
      />
      {!card.is_eclipse && (
        <p className="ss-note">
          No eclipse is visible here at this new moon. Try October 2024, or another place.
        </p>
      )}
      {card.is_eclipse && card.locally_visible === false && (
        <p className="ss-note">
          The discs overlap from this place, but the Sun is below the horizon at the
          conjunction, so the eclipse is not seen here.
        </p>
      )}
    </>
  );
}
