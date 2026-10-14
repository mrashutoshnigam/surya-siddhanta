import { useState } from "react";
import { api } from "../api";
import { ErrorBox, GridTable, PageHeader } from "../components/Tables";

const HELIACAL_PLANETS = ["Mars", "Mercury", "Jupiter", "Venus", "Saturn"];

interface Event {
  type: string;
  date: string;
  elongation: number;
  direction: string;
}

interface HeliacalResult {
  events: Event[];
  summary: string;
}

export function Heliacal() {
  const [planet, setPlanet] = useState("Venus");
  const [year, setYear] = useState(new Date().getFullYear());
  const [months, setMonths] = useState(12);
  const [result, setResult] = useState<HeliacalResult | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);

  function search() {
    setLoading(true);
    api
      .heliacal({ planet, year, months })
      .then((r) => {
        setResult(r as HeliacalResult);
        setError(null);
      })
      .catch(setError)
      .finally(() => setLoading(false));
  }

  return (
    <div>
      <PageHeader title="Heliacal Events" subtitle="First and last visibility of a planet near the Sun (Ch.9)" />
      <div className="field-row">
        <label>
          Planet
          <select value={planet} onChange={(e) => setPlanet(e.target.value)}>
            {HELIACAL_PLANETS.map((p) => (
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
          <input type="number" value={months} min={1} max={36} onChange={(e) => setMonths(Number(e.target.value))} />
        </label>
        <button onClick={search} disabled={loading}>
          {loading ? "Scanning…" : "Search"}
        </button>
      </div>
      <ErrorBox error={error} />
      {result &&
        (result.events.length === 0 ? (
          <p className="ss-note">{result.summary}</p>
        ) : (
          <>
            <p className="ss-note">{result.summary}</p>
            <GridTable
              headers={["Date", "Event", "Elongation", "Direction"]}
              rows={result.events.map((ev) => [ev.date, ev.type, `${ev.elongation.toFixed(1)}°`, ev.direction])}
            />
          </>
        ))}
    </div>
  );
}
