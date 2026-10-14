import { useState } from "react";
import { KVTable } from "../../../components/Tables";
import { Slider } from "../../../components/VerseCard";
import { fmt } from "../ch01/scale";
import { useLastProbe } from "./probe";
import type { DayLength, DayLengthCard } from "./types";

/**
 * ii.60-63 — the day-radius and the length of the day.
 *
 * The day-radius is the radius less the versed sine of the Sun's
 * declination. Latitude and the Sun's tropical longitude are both free, so
 * the seasons and the latitudes can be walked through.
 */
export function V60DayLength({ card }: { card: DayLengthCard }) {
  const [latitude, setLatitude] = useState(card.latitude);
  const [sun, setSun] = useState(card.sun_tropical);
  const result = useLastProbe<DayLength>(
    { card: "ii.60-63", latitude, sun_longitude: sun },
    card,
  );

  return (
    <>
      <Slider label="Sun's longitude (tropical)" value={sun} min={0} max={360} step={1} suffix="°" onChange={setSun} />
      <Slider label="Latitude" value={latitude} min={-90} max={90} step={0.5} suffix="°" onChange={setLatitude} />
      <KVTable
        rows={[
          ["Declination", `${fmt(Math.abs(result.declination))}° ${result.direction}`],
          ["Sine · versed sine of it", `${fmt(result.sine_declination)} · ${fmt(result.versed_sine)}`],
          ["Day-radius (R − versed sine)", <strong>{fmt(result.day_radius)}</strong>],
          ["Day", `${fmt(result.day_ghatis)} ghatis — ${fmt(result.day_ghatis * 0.4)} h`],
          ["Night", `${fmt(result.night_ghatis)} ghatis — ${fmt(result.night_ghatis * 0.4)} h`],
        ]}
      />
      <p className="verse-note">
        Day and night follow the library&apos;s hour-angle formula, not the text&apos;s tabular rule.
      </p>
    </>
  );
}
