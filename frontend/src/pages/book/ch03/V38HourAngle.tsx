import { useState } from "react";
import { KVTable } from "../../../components/Tables";
import { Slider } from "../../../components/VerseCard";
import { fmt } from "../ch01/scale";
import { useLastProbe } from "./probe";
import type { HourAngleCard, HourAngleResult } from "./types";

/** iii.38-41 — the Sun's altitude, azimuth and shadow at an hour angle from noon. */
export function V38HourAngle({ card }: { card: HourAngleCard }) {
  const [latitude, setLatitude] = useState(card.latitude);
  const [declination, setDeclination] = useState(card.declination);
  const [hourAngle, setHourAngle] = useState(card.hour_angle);
  const result = useLastProbe<HourAngleResult>(
    { card: "iii.38-41", latitude, declination, hour_angle: hourAngle },
    card,
  );

  return (
    <>
      <Slider label="Latitude" value={latitude} min={-90} max={90} step={0.5} suffix="°" onChange={setLatitude} />
      <Slider label="Declination" value={declination} min={-24} max={24} step={0.5} suffix="°" onChange={setDeclination} />
      <Slider label="Hour angle from noon" value={hourAngle} min={-180} max={180} step={1} suffix="°" onChange={setHourAngle} />
      <KVTable
        rows={[
          ["Time from noon", `${fmt(Math.abs(result.hour_angle) / 15)} h`],
          ["Altitude", <strong>{fmt(result.altitude)}°</strong>],
          ["Azimuth, from north", `${fmt(result.azimuth)}°`],
          ["Shadow", result.altitude <= 0 || result.shadow === null ? "none — the Sun is below the horizon" : `${fmt(result.shadow)} digits`],
        ]}
      />
    </>
  );
}
