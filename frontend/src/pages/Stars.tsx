import { useEffect, useState } from "react";
import { api } from "../api";
import { DateInput, DateValue, DEFAULT_LATLON, LatLon, LatLonInput, todayValue } from "../components/Inputs";
import { ErrorBox, KVTable, PageHeader } from "../components/Tables";
import { SkyMap } from "../components/SkyMap";

const NAKSHATRAS = [
  "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
  "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
  "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
  "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta",
  "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
];

interface StarsResult {
  info: {
    name: string; devanagari: string; star: string; deity: string; gana: string;
    span_start: number; span_end: number;
  };
  position: {
    sidereal_longitude: number; sidereal_latitude: number; tropical_longitude: number;
    right_ascension: number; declination: number;
  };
  rise_set: { is_circumpolar: boolean; is_never_visible: boolean; summary: string };
  sky_map: { name: string; right_ascension: number; declination: number }[];
}

export function Stars() {
  const [name, setName] = useState("Rohini");
  const [date, setDate] = useState<DateValue>(todayValue());
  const [latlon, setLatlon] = useState<LatLon>(DEFAULT_LATLON);
  const [result, setResult] = useState<StarsResult | null>(null);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    api
      .stars({ nakshatra: name, ...date, ...latlon })
      .then((r) => {
        setResult(r as StarsResult);
        setError(null);
      })
      .catch(setError);
  }, [name, date.year, date.month, date.day, latlon.latitude, latlon.longitude]);

  return (
    <div>
      <PageHeader title="Stars" subtitle="Yogatara positions, rise/set and the sky map (Ch.8)" />
      <div className="field-row">
        <label>
          Nakshatra / yogatara
          <select value={name} onChange={(e) => setName(e.target.value)}>
            {NAKSHATRAS.map((n) => (
              <option key={n}>{n}</option>
            ))}
          </select>
        </label>
      </div>
      <DateInput value={date} onChange={setDate} withZone />
      <LatLonInput value={latlon} onChange={setLatlon} />
      <ErrorBox error={error} />
      {result && (
        <>
          <KVTable
            title={`Yogatara — ${name}`}
            rows={[
              ["Nakshatra", `${result.info.name} (${result.info.devanagari})`],
              ["Junction star", result.info.star],
              ["Deity / Gana", `${result.info.deity} / ${result.info.gana}`],
              ["Span", `${result.info.span_start.toFixed(2)}° – ${result.info.span_end.toFixed(2)}°`],
              ["Sidereal", `lon ${result.position.sidereal_longitude.toFixed(2)}°, lat ${result.position.sidereal_latitude.toFixed(2)}°`],
              ["Tropical lon", `${result.position.tropical_longitude.toFixed(2)}°`],
              ["Equatorial", `RA ${result.position.right_ascension.toFixed(2)}°, Dec ${result.position.declination.toFixed(2)}°`],
              ["Rise / Set", result.rise_set.summary],
            ]}
          />
          <div className="chart-block">
            <SkyMap stars={result.sky_map} highlight={name} />
          </div>
        </>
      )}
    </div>
  );
}
