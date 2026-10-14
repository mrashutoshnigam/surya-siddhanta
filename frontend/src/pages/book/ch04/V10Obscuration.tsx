import { useState } from "react";
import { KVTable } from "../../../components/Tables";
import { Slider } from "../../../components/VerseCard";
import { fmt } from "../ch01/scale";
import { useLastProbe } from "./probe";
import type { Geometry, ObscurationCard } from "./types";

const VERDICT = { total: "total", partial: "partial", none: "no eclipse" } as const;

/**
 * iv.10-11 — the amount obscured.
 *
 * Half the sum of the eclipsed and eclipsing disks, less the Moon's latitude.
 * The slider starts at this full moon's latitude and can be moved to see where
 * the eclipse turns partial or vanishes.
 */
export function V10Obscuration({ card }: { card: ObscurationCard }) {
  const [latitude, setLatitude] = useState(card.latitude);
  const result = useLastProbe<Geometry>(
    {
      card: "iv.10-11",
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
          ["Half the sum of the disks", `${fmt(result.half_sum)}′`],
          [
            "Less the latitude",
            result.eclipse_type === "none"
              ? "nothing — the latitude exceeds the half-sum"
              : `${fmt(result.obscured)}′ obscured`,
          ],
          ["Magnitude", fmt(result.magnitude)],
          ["Verdict", <strong>{VERDICT[result.eclipse_type]}</strong>],
        ]}
      />
    </>
  );
}
