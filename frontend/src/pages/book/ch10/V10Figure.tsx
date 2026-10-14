import { KVTable } from "../../../components/Tables";
import { fmt } from "../ch01/scale";
import { MoonDisc } from "./MoonDisc";
import type { FigureCard } from "./types";

/**
 * x.10-14 — the figure of the Moon.
 *
 * The verses draw the Sun, lay the base and perpendicular off from it, and
 * describe the Moon's disc about their meeting, with the lit part laid along
 * the hypotenuse and the cusps drawn as arcs. The library does not follow
 * that construction; it gives the Moon's bright-limb position angle and the
 * horn angle for the place, which fix the same figure: how much of the disc
 * is lit, and which way the cusps point. The strip shows the following week.
 */
export function V10Figure({ card }: { card: FigureCard }) {
  const now = card.now;
  return (
    <>
      <div style={{ display: "flex", gap: 24, alignItems: "center", flexWrap: "wrap" }}>
        <MoonDisc elongation={now.elongation} sunAngle={now.sun_angle} size={180} />
        <KVTable
          rows={[
            ["Phase", now.phase],
            ["Elongation", `${fmt(now.elongation)}°`],
            ["Bright limb, from the north", `${fmt(now.bright_limb_angle)}°`],
            ["Horn axis, for the place", `${fmt(now.horn_angle)}°`],
            ["Sun lies at (in the figure)", `${fmt(now.sun_angle)}° clockwise from the top`],
          ]}
        />
      </div>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 12 }}>
        {card.strip.map((c, i) => (
          <figure key={c.jd} style={{ margin: 0, textAlign: "center" }}>
            <MoonDisc elongation={c.elongation} sunAngle={c.sun_angle} size={70} />
            <figcaption className="ss-note">
              {i === 0 ? "today" : `+${i} d`}
              <br />
              {fmt(c.fraction)}
            </figcaption>
          </figure>
        ))}
      </div>
      <p className="ss-note">
        Sun to the right of the lit limb. The dashed line is the axis joining the Moon to the Sun;
        the cusps lie across it. The number under each small Moon is the lit fraction.
      </p>
    </>
  );
}
