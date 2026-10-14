import { useEffect, useState } from "react";
import { api } from "../api";
import { DateInput, DateValue, DEFAULT_LATLON, LatLon, LatLonInput, todayValue } from "../components/Inputs";
import { ErrorBox, KVTable, PageHeader } from "../components/Tables";

interface PlaceTimeResult {
  ahargana: { julian_day: number; ahargana: number; kali_era_year: number; kali_years: number; vara: string };
  ayanamsha: { ayanamsha_degrees: number };
  day_length: { day_length_ghatis: number; night_length_ghatis: number; day_length_hours: number; declination: number };
  lagna: { lagna_longitude: number; rashi_name: string };
  gnomon: { altitude: number; shadow_length: number | null };
}

export function PlaceTime() {
  const [date, setDate] = useState<DateValue>(todayValue());
  const [latlon, setLatlon] = useState<LatLon>(DEFAULT_LATLON);
  const [gnomonAltitude, setGnomonAltitude] = useState(45);
  const [result, setResult] = useState<PlaceTimeResult | null>(null);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    api
      .placeTime({ ...date, ...latlon, gnomon_altitude: gnomonAltitude })
      .then((r) => {
        setResult(r as PlaceTimeResult);
        setError(null);
      })
      .catch(setError);
  }, [date.year, date.month, date.day, latlon.latitude, latlon.longitude, gnomonAltitude]);

  return (
    <div>
      <PageHeader title="Place & Time" subtitle="Time reckoning, day/night length, ascendant and shadow (Ch.1, Ch.3)" />
      <DateInput value={date} onChange={setDate} withZone />
      <LatLonInput value={latlon} onChange={setLatlon} />
      <div className="field-row">
        <label>
          Sun altitude for gnomon (°)
          <input
            type="number"
            value={gnomonAltitude}
            min={0}
            max={90}
            onChange={(e) => setGnomonAltitude(Number(e.target.value))}
          />
        </label>
      </div>
      <ErrorBox error={error} />
      {result && (
        <div className="two-col">
          <KVTable
            title="Time Reckoning (Ch.1)"
            rows={[
              ["Julian Day", result.ahargana.julian_day.toFixed(4)],
              ["Ahargana", result.ahargana.ahargana.toFixed(2)],
              ["Kali era year", String(result.ahargana.kali_era_year)],
              ["Kali years elapsed (since epoch)", result.ahargana.kali_years.toFixed(4)],
              ["Ayanamsha", `${result.ayanamsha.ayanamsha_degrees.toFixed(4)}°`],
              [
                "Gnomon shadow",
                result.gnomon.shadow_length == null
                  ? "Sun below horizon"
                  : `${result.gnomon.shadow_length.toFixed(3)} digits`,
              ],
            ]}
          />
          <KVTable
            title="Direction, Place & Time (Ch.3)"
            rows={[
              ["Day length", `${result.day_length.day_length_ghatis.toFixed(2)} ghatis (${result.day_length.day_length_hours.toFixed(2)} h)`],
              ["Night length", `${result.day_length.night_length_ghatis.toFixed(2)} ghatis`],
              ["Sun declination", `${result.day_length.declination.toFixed(4)}°`],
              ["Lagna (ascendant)", `${result.lagna.lagna_longitude.toFixed(2)}° — ${result.lagna.rashi_name}`],
            ]}
          />
        </div>
      )}
    </div>
  );
}
