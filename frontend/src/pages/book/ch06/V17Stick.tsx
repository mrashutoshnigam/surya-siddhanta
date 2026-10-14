import { useState } from "react";
import { KVTable } from "../../../components/Tables";
import { Picker, Slider } from "../../../components/VerseCard";
import { fmt } from "../ch01/scale";
import { ProjectionSvg } from "./ProjectionSvg";
import { useLastProbe } from "./probe";
import type { StickCard, StickProbe } from "./types";

/**
 * vi.17-19 — the stick for a given time.
 *
 * Half the sum of the bodies less the amount obscured at the chosen moment
 * is the length of a little stick. Laid from the centre to the path, on the
 * contact side before the middle and the separation side after (v.18), it
 * meets the path at the eclipser's centre; the circle about that point shows
 * what is swallowed (v.19).
 */
export function V17Stick({ card }: { card: StickCard }) {
  const [obscured, setObscured] = useState(card.default_obscured ?? 0);
  const [side, setSide] = useState<"contact" | "separation">("contact");
  const answer = useLastProbe<StickProbe | null>(
    {
      card: "vi.17-19",
      kind: card.kind,
      eclipsed_radius: card.eclipsed_radius,
      eclipser_radius: card.eclipser_radius,
      latitude_arcmin: card.latitude,
      obscured,
      side,
    },
    null,
  );

  if (!card.is_eclipse) {
    return <p className="ss-note">There is no eclipse at this date, so no stick reaches the path.</p>;
  }
  return (
    <>
      <Slider
        label="Amount obscured at that time"
        value={obscured}
        min={0}
        max={Math.floor(card.obscured * 100) / 100}
        step={0.1}
        suffix="′"
        onChange={setObscured}
      />
      <Picker
        label="Side of the path"
        value={side}
        options={[
          { value: "contact", label: "before the middle (contact)" },
          { value: "separation", label: "after the middle (separation)" },
        ]}
        onChange={setSide}
      />
      <ProjectionSvg
        eclipsedR={card.eclipsed_radius}
        eclipserR={card.eclipser_radius}
        valana={card.valana}
        contact={card.contact}
        middle={card.middle}
        separation={card.separation}
        marks={[{ point: answer?.point ?? null, label: "stick" }]}
      />
      <KVTable
        rows={[
          ["Half the sum", `${fmt(card.half_sum)}′`],
          ["Stick (half the sum − obscured)", <strong>{fmt(card.half_sum - obscured)}′</strong>],
          [
            "Eclipser's centre",
            answer?.point
              ? `${fmt(answer.point[0])}′ along, ${fmt(answer.point[1])}′ across`
              : "the stick is too short to reach the path",
          ],
        ]}
      />
    </>
  );
}
