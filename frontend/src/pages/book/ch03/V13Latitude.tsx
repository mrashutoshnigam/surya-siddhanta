import { useState } from "react";
import { KVTable } from "../../../components/Tables";
import { Slider } from "../../../components/VerseCard";
import { fmt } from "../ch01/scale";
import { useLastProbe } from "./probe";
import type { LatitudeCard, LatitudeResult } from "./types";

/**
 * iii.13-17 — the latitude from the noon shadow.
 *
 * Seeded with the noon shadow cast at the page's latitude for the date's
 * Sun; the library's inverse should return that latitude. Move either
 * slider to ask what a different shadow or season would say.
 */
export function V13Latitude({ card }: { card: LatitudeCard }) {
  const [shadow, setShadow] = useState(card.shadow);
  const [sun, setSun] = useState(card.sun_tropical);
  const [shadowDirection, setShadowDirection] = useState(card.shadow_direction);
  const result = useLastProbe<LatitudeResult>(
    { card: "iii.13-17", shadow, sun_longitude: sun, shadow_direction: shadowDirection },
    card,
  );

  return (
    <>
      <Slider label="Noon shadow" value={shadow} min={0} max={60} step={0.1} suffix="digits" onChange={setShadow} />
      <Slider label="Sun's longitude (tropical)" value={sun} min={0} max={360} step={1} suffix="°" onChange={setSun} />
      <label>
        Noon shadow points
        <select value={shadowDirection} onChange={(e) => setShadowDirection(e.target.value as "north" | "south")}>
          <option value="north">North</option>
          <option value="south">South</option>
        </select>
      </label>
      <KVTable
        rows={[
          ["Sun's altitude at noon", `${fmt(result.altitude)}°`],
          ["Sun's declination", `${fmt(result.declination)}°`],
          ["Latitude", <strong>{fmt(result.latitude)}°</strong>],
        ]}
      />
      <p className="verse-note">
        The shadow shown first is the noon shadow at {fmt(card.latitude_true)}° for this date.
      </p>
    </>
  );
}
