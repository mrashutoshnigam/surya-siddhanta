import { useState } from "react";
import { KVTable } from "../../../components/Tables";
import { Slider } from "../../../components/VerseCard";
import { fmt, grouped } from "../ch01/scale";
import { useLastProbe } from "./probe";
import type { InterpForward, InterpInverse, InterpolationCard } from "./types";

/**
 * ii.31-33 — interpolating between tabular sines, and back.
 *
 * Both directions run through the library (``ch02.jya`` / ``arcjya``) and are
 * shown step by step as the verses state them.
 */
export function V31Interpolation({ card }: { card: InterpolationCard }) {
  const [arc, setArc] = useState(card.forward.arc_deg);
  const [sine, setSine] = useState(card.inverse.sine);
  const forward = useLastProbe<InterpForward>(
    { card: "ii.31-33", mode: "forward", arc_deg: arc },
    card.forward,
  );
  const inverse = useLastProbe<InterpInverse>(
    { card: "ii.31-33", mode: "inverse", sine },
    card.inverse,
  );

  return (
    <>
      <h3>The sine of an arc (v.31-32)</h3>
      <Slider label="Arc" value={arc} min={0} max={90} step={0.05} suffix="°" onChange={setArc} />
      <KVTable
        rows={[
          ["Minutes of arc", `${fmt(forward.arcmin)}′`],
          [`÷ ${card.step_arcmin}′`, `quotient ${forward.quotient}, remainder ${fmt(forward.remainder_arcmin)}′`],
          ["Preceding · next tabular sine", `${grouped(forward.preceding)} · ${grouped(forward.following)}`],
          ["Difference", grouped(forward.difference)],
          ["Remainder × difference ÷ 225", fmt(forward.part)],
          ["Sine (interpolated)", <strong>{fmt(forward.interpolated)}</strong>],
          ["Library jya · exact R·sin", `${fmt(forward.library)} · ${fmt(forward.exact)}`],
        ]}
      />

      <h3>The arc of a sine (v.33)</h3>
      <Slider label="Sine" value={sine} min={0} max={3438} step={1} onChange={setSine} />
      <KVTable
        rows={[
          ["Tabular sines below it", inverse.count_below],
          ["Next less tabular sine", grouped(inverse.less)],
          ["Difference to the next", grouped(inverse.difference)],
          ["Arc", <strong>{fmt(inverse.arcmin)}′ = {fmt(inverse.arc_deg)}°</strong>],
          ["Library arcjya", `${fmt(inverse.library_deg)}°`],
        ]}
      />
    </>
  );
}
