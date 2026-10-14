import { KVTable } from "../../../components/Tables";
import { fmt } from "../ch01/scale";
import { ProjectionSvg } from "./ProjectionSvg";
import type { StickCard } from "./types";

/**
 * vi.20-22 — immersion and emergence.
 *
 * A stick of half the difference of the two bodies is laid toward contact
 * (the stick of immersion) and toward separation (emergence). Where it
 * meets the path, a circle of the eclipser's radius touches the eclipsed
 * disk's rim from inside: the moment the whole disk is just covered, or just
 * begins to clear. A partial eclipse never has them.
 */
export function V20Immersion({ card }: { card: StickCard }) {
  if (!card.is_eclipse) {
    return <p className="ss-note">There is no eclipse at this date.</p>;
  }
  return (
    <>
      <ProjectionSvg
        eclipsedR={card.eclipsed_radius}
        eclipserR={card.eclipser_radius}
        valana={card.valana}
        contact={card.contact}
        middle={card.middle}
        separation={card.separation}
        marks={[
          { point: card.contact_point, label: "immersion" },
          { point: card.separation_point, label: "emergence" },
        ]}
      />
      <KVTable
        rows={[
          ["Stick of immersion (half the difference)", `${fmt(card.stick ?? 0)}′`],
          [
            "Immersion and emergence",
            <strong>
              {card.has_immersion
                ? `occur (the eclipse is ${card.eclipse_type})`
                : "do not occur — the eclipse is partial"}
            </strong>,
          ],
        ]}
      />
    </>
  );
}
