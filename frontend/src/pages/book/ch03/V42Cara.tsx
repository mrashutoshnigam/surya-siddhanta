import { useState } from "react";
import { KVTable } from "../../../components/Tables";
import { Slider } from "../../../components/VerseCard";
import { fmt } from "../ch01/scale";
import { useLastProbe } from "./probe";
import type { CaraCard, CaraResult } from "./types";

/** iii.42 — the ascensional difference (cara) and the resulting day and night. */
export function V42Cara({ card }: { card: CaraCard }) {
  const [latitude, setLatitude] = useState(card.latitude);
  const [sun, setSun] = useState(card.sun_tropical);
  const result = useLastProbe<CaraResult>(
    { card: "iii.42", latitude, sun_longitude: sun },
    card,
  );

  return (
    <>
      <Slider label="Sun's longitude (tropical)" value={sun} min={0} max={360} step={1} suffix="°" onChange={setSun} />
      <Slider label="Latitude" value={latitude} min={-90} max={90} step={0.5} suffix="°" onChange={setLatitude} />
      <KVTable
        rows={[
          ["Declination", `${fmt(result.declination)}°`],
          ["Cara", `${fmt(result.cara_ghatis)} ghatis`],
          ["Half-day (15 + cara)", `${fmt(result.half_day_ghatis)} ghatis`],
          ["Sunrise, from noon", `${fmt(result.sunrise_hour_angle)}° — ${fmt(result.sunrise_offset_hours)} h`],
          ["Day", <strong>{fmt(result.day_ghatis)} ghatis</strong>],
          ["Night", `${fmt(result.night_ghatis)} ghatis`],
        ]}
      />
    </>
  );
}
