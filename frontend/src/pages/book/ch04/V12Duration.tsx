import { useState } from "react";
import { KVTable } from "../../../components/Tables";
import { Slider } from "../../../components/VerseCard";
import { fmt } from "../ch01/scale";
import { useLastProbe } from "./probe";
import type { DurationCard, Geometry } from "./types";

/** Format minutes as minutes and ghatis, or a dash when there is no such phase. */
function span(minutes: number | null, ghatis: number | null): string {
  return minutes === null || ghatis === null ? "—" : `${fmt(minutes)} min — ${fmt(ghatis)} ghatis`;
}

/**
 * iv.12-13 — the half-duration and half-totality.
 *
 * The square roots of half-sum² and half-difference², each less latitude²,
 * divided by the relative daily motion of Moon and Sun. The library's single
 * pass is shown; the text's iteration (v.15) is not.
 */
export function V12Duration({ card }: { card: DurationCard }) {
  const [latitude, setLatitude] = useState(card.latitude);
  const result = useLastProbe<Geometry>(
    {
      card: "iv.12-13",
      moon_diameter: card.moon_diameter,
      shadow_diameter: card.shadow_diameter,
      latitude_arcmin: latitude,
    },
    card,
  );

  return (
    <>
      <Slider label="Moon's latitude" value={latitude} min={-270} max={270} step={1} suffix="′" onChange={setLatitude} />
      <KVTable
        rows={[
          ["√(half-sum² − latitude²)", result.root_sum === null ? "—" : `${fmt(result.root_sum)}′`],
          ["√(half-difference² − latitude²)", result.root_difference === null ? "—" : `${fmt(result.root_difference)}′`],
          ["Relative motion of Moon and Sun", `${fmt(result.speed_arcmin_per_min)}′ a minute`],
          ["Half the eclipse", <strong>{span(result.half_duration_min, result.half_duration_ghatis)}</strong>],
          ["Half the totality", span(result.totality_half_min, result.totality_half_ghatis)],
        ]}
      />
    </>
  );
}
