import { KVTable } from "../../../components/Tables";
import { fmt } from "../ch01/scale";
import { ProjectionSvg } from "./ProjectionSvg";
import type { PathCard } from "./types";

/**
 * vi.14-16 — the path of the eclipser.
 *
 * Points are made at the three latitudes (contact, middle, separation);
 * fish-figures between them give two cross-lines and an arc through the
 * three points. The library draws the path as a straight chord of the
 * aggregate circle, which is what the line below is.
 */
export function V14Path({ card }: { card: PathCard }) {
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
      {card.is_eclipse && card.contact && card.separation ? (
        <KVTable
          rows={[
            ["Eclipser's centre at contact", `${fmt(card.contact[0])}′ along, ${fmt(card.contact[1])}′ across`],
            ["…at the middle", `${fmt(card.middle[0])}′ along, ${fmt(card.middle[1])}′ across`],
            ["…at separation", `${fmt(card.separation[0])}′ along, ${fmt(card.separation[1])}′ across`],
            ["Length of the path across the aggregate circle", <strong>{fmt(card.chord_length ?? 0)}′</strong>],
          ]}
        />
      ) : (
        <p className="ss-note">There is no eclipse at this date, so there is no path through the disk.</p>
      )}
    </>
  );
}
