import { useState } from "react";
import { api } from "../api";
import { ErrorBox, GridTable, PageHeader } from "../components/Tables";

const PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"];

interface Conjunction {
  date: string;
  jd: number;
  longitude: number;
  separation_deg: number;
  type: string;
}

interface ConjunctionsResult {
  conjunctions: Conjunction[];
  summary: string;
}

export function Conjunctions() {
  const [planet1, setPlanet1] = useState("Mars");
  const [planet2, setPlanet2] = useState("Jupiter");
  const [year, setYear] = useState(new Date().getFullYear());
  const [months, setMonths] = useState(12);
  const [result, setResult] = useState<ConjunctionsResult | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);

  function search() {
    setLoading(true);
    api
      .conjunctions({ planet1, planet2, year, months })
      .then((r) => {
        setResult(r as ConjunctionsResult);
        setError(null);
      })
      .catch(setError)
      .finally(() => setLoading(false));
  }

  return (
    <div>
      <PageHeader title="Conjunctions" subtitle="Planet–planet conjunctions over a time period (Ch.7)" />
      <div className="field-row">
        <label>
          Planet 1
          <select value={planet1} onChange={(e) => setPlanet1(e.target.value)}>
            {PLANETS.map((p) => (
              <option key={p}>{p}</option>
            ))}
          </select>
        </label>
        <label>
          Planet 2
          <select value={planet2} onChange={(e) => setPlanet2(e.target.value)}>
            {PLANETS.map((p) => (
              <option key={p}>{p}</option>
            ))}
          </select>
        </label>
        <label>
          Year
          <input type="number" value={year} onChange={(e) => setYear(Number(e.target.value))} />
        </label>
        <label>
          Search span (months)
          <input type="number" value={months} min={1} max={60} onChange={(e) => setMonths(Number(e.target.value))} />
        </label>
        <button onClick={search} disabled={loading}>
          {loading ? "Searching…" : "Search"}
        </button>
      </div>
      <ErrorBox error={error} />
      {result && (
        <>
          <p className="ss-note">{result.summary}</p>
          <GridTable
            headers={["Date", "Longitude", "Separation", "Type"]}
            rows={result.conjunctions.map((c) => [
              c.date,
              `${c.longitude.toFixed(2)}°`,
              `${c.separation_deg.toFixed(3)}°`,
              c.type,
            ])}
          />
        </>
      )}
    </div>
  );
}
