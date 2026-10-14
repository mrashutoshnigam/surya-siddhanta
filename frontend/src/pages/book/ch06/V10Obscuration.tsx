import { KVTable } from "../../../components/Tables";
import { fmt } from "../ch01/scale";
import { ProjectionSvg } from "./ProjectionSvg";
import type { ObscurationCard } from "./types";

const VERDICT = { total: "total", annular: "annular", partial: "partial", none: "no eclipse" } as const;

/**
 * vi.10-11 — the latitude, and what the eclipser's circle covers.
 *
 * From the end of the deflection a line is drawn to the centre and the
 * latitude laid off on it; a circle of the eclipser's radius about that
 * point swallows whatever part of the disk it encloses.
 */
export function V10Obscuration({ card }: { card: ObscurationCard }) {
  return (
    <>
      <ProjectionSvg
        eclipsedR={card.eclipsed_radius}
        eclipserR={card.eclipser_radius}
        valana={card.valana}
        contact={card.contact}
        middle={card.middle}
        separation={card.separation}
      />
      <KVTable
        rows={[
          [
            "Latitude at the middle",
            `${fmt(Math.abs(card.middle_latitude))}′ ${card.middle_latitude >= 0 ? "north" : "south"}`,
          ],
          ["Radius of the eclipser's circle", `${fmt(card.circle_radius)}′`],
          [
            "Half the sum less the latitude",
            card.is_eclipse ? `${fmt(card.obscured)}′ swallowed` : "nothing — the latitude is too great",
          ],
          ["Magnitude", fmt(card.magnitude)],
          ["Verdict", <strong>{VERDICT[card.eclipse_type]}</strong>],
        ]}
      />
    </>
  );
}
