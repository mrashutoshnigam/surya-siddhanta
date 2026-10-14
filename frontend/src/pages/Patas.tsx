import { useState } from "react";
import { api } from "../api";
import { ErrorBox, GridTable, PageHeader } from "../components/Tables";

interface PataEvent {
  kind: string;
  begin: string;
  middle: string;
  end: string;
  nominal_crossing: string;
  duration_ghatis: number;
  sun_declination: number;
  moon_declination: number;
  moon_latitude_arcmin: number;
}

interface PatasResult {
  events: PataEvent[];
  count: number;
  summary: string;
}

export function Patas() {
  const today = new Date();
  const [year, setYear] = useState(today.getFullYear());
  const [month, setMonth] = useState(today.getMonth() + 1);
  const [day, setDay] = useState(today.getDate());
  const [days, setDays] = useState(60);
  const [result, setResult] = useState<PatasResult | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);

  function search() {
    setLoading(true);
    api
      .patas({ year, month, day, days })
      .then((r) => {
        setResult(r as PatasResult);
        setError(null);
      })
      .catch(setError)
      .finally(() => setLoading(false));
  }

  return (
    <div>
      <PageHeader
        title="Patas"
        subtitle="Vyatipata and Vaidhrita — when the Sun's and Moon's declinations become equal in amount (Ch.11)"
      />
      <div className="field-row">
        <label>
          Year
          <input type="number" value={year} onChange={(e) => setYear(Number(e.target.value))} />
        </label>
        <label>
          Month
          <input type="number" min={1} max={12} value={month} onChange={(e) => setMonth(Number(e.target.value))} />
        </label>
        <label>
          Day
          <input type="number" min={1} max={31} value={day} onChange={(e) => setDay(Number(e.target.value))} />
        </label>
        <label>
          Search span (days)
          <input type="number" min={7} max={365} value={days} onChange={(e) => setDays(Number(e.target.value))} />
        </label>
        <button onClick={search} disabled={loading}>
          {loading ? "Scanning…" : "Search"}
        </button>
      </div>
      <ErrorBox error={error} />
      {result && (
        <>
          <p className="ss-note">{result.summary}</p>
          {result.events.length > 0 && (
            <GridTable
              headers={[
                "Pata",
                "Begins",
                "Middle",
                "Ends",
                "Ghatis",
                "Sun dec.",
                "Moon dec.",
                "Moon lat.",
                "Nominal (sum rule)",
              ]}
              rows={result.events.map((ev) => [
                ev.kind,
                ev.begin,
                ev.middle,
                ev.end,
                ev.duration_ghatis.toFixed(1),
                `${ev.sun_declination.toFixed(2)}°`,
                `${ev.moon_declination.toFixed(2)}°`,
                `${ev.moon_latitude_arcmin.toFixed(1)}′`,
                ev.nominal_crossing,
              ])}
            />
          )}
        </>
      )}
    </div>
  );
}
