import { useEffect, useState } from "react";
import { api } from "../api";
import { DateInput, DateValue, todayValue } from "../components/Inputs";
import { ErrorBox, GridTable, PageHeader } from "../components/Tables";
import { ZodiacWheel } from "../components/ZodiacWheel";

const ALL_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"];

interface PlanetRow {
  planet: string;
  true_longitude: number;
  mean_longitude: number;
  tropical_longitude: number;
  rashi: { name: string; degrees: number };
  nakshatra: { name: string; pada: number };
}

interface AllPlanetsResult {
  jd: number;
  ahargana: number;
  ayanamsha: number;
  planets: PlanetRow[];
}

export function PlanetPositions() {
  const [date, setDate] = useState<DateValue>(todayValue());
  const [selected, setSelected] = useState<string[]>(ALL_PLANETS);
  const [result, setResult] = useState<AllPlanetsResult | null>(null);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    api
      .allPlanets({ ...date, planets: selected.length ? selected : undefined })
      .then((r) => {
        setResult(r as AllPlanetsResult);
        setError(null);
      })
      .catch(setError);
  }, [date.year, date.month, date.day, selected.join(",")]);

  function toggle(p: string) {
    setSelected((s) => (s.includes(p) ? s.filter((x) => x !== p) : [...s, p]));
  }

  return (
    <div>
      <PageHeader title="Planet Positions" subtitle="Mean and true longitudes on the sidereal zodiac (Ch.1–2)" />
      <DateInput value={date} onChange={setDate} withZone />
      <div className="chip-row">
        {ALL_PLANETS.map((p) => (
          <label key={p} className="chip">
            <input type="checkbox" checked={selected.includes(p)} onChange={() => toggle(p)} />
            {p}
          </label>
        ))}
      </div>
      <ErrorBox error={error} />
      {result && (
        <>
          <p className="ss-note">
            JD {result.jd.toFixed(2)} (Ujjain mean time) · Ahargana {result.ahargana.toFixed(2)} · Ayanamsha{" "}
            {result.ayanamsha.toFixed(4)}°
          </p>
          <GridTable
            headers={["Planet", "True longitude", "Mean lon", "Tropical lon", "Rashi", "Nakshatra"]}
            rows={result.planets.map((p) => [
              <strong>{p.planet}</strong>,
              `${p.true_longitude.toFixed(4)}°`,
              `${p.mean_longitude.toFixed(4)}°`,
              `${p.tropical_longitude.toFixed(4)}°`,
              `${p.rashi.name} ${p.rashi.degrees?.toFixed?.(2) ?? ""}°`,
              `${p.nakshatra.name} p${p.nakshatra.pada}`,
            ])}
          />
          <div className="chart-block">
            <ZodiacWheel planets={result.planets} />
          </div>
        </>
      )}
    </div>
  );
}
