import { GridTable } from "../../../components/Tables";
import { fmt } from "../ch01/scale";
import type { OrbitsCard } from "./types";

const whole = (n: number) => Math.round(n).toLocaleString();

/**
 * xii.80-90 — the orbits of the planets.
 *
 * Every planet covers the same distance in a kalpa, so an orbit is
 * proportional to the time round it, scaled so the Moon's is 324,000
 * yojanas. Revolutions here are per kalpa, not per mahayuga. Burgess notes
 * the premise is false and only the Moon's figure was truly calculated. The
 * text's own stated figures differ from the rule by up to about 1.3 yojanas
 * through rounding, shown in the last column.
 */
export function V80Orbits({ card }: { card: OrbitsCard }) {
  return (
    <>
      <p className="ss-note">
        Same daily motion for every body: {fmt(card.daily_linear_motion)} yojanas. The ether&apos;s
        orbit, bounding the Sun&apos;s rays: {whole(card.ether_orbit)} yojanas.
      </p>
      <div className="table-scroll">
        <GridTable
          headers={["Body", "Revolutions per kalpa", "Orbit (yojanas)", "Diameter", "Distance", "Daily motion", "Orbit less text's"]}
          rows={card.orbits.map((o) => [
            o.body.replace(/_/g, " "),
            whole(o.revolutions_per_kalpa),
            whole(o.orbit_yojanas),
            whole(o.orbit_diameter_yojanas),
            whole(o.distance_yojanas),
            `${fmt(o.daily_motion_arcmin)}′`,
            o.stated_difference == null ? "—" : fmt(o.stated_difference),
          ])}
        />
      </div>
    </>
  );
}
