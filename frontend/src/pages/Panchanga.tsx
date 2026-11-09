import { useEffect, useState } from "react";
import { api } from "../api";
import { currentDateTimeValue, DateInput, DateValue } from "../components/Inputs";
import { ErrorBox, KVTable, PageHeader } from "../components/Tables";

interface PanchangaResult {
  at: string;
  tithi: { number: number; name: string; paksha: string; fraction: number };
  vara: { number: number; name: string };
  nakshatra: { number: number; name: string; pada: number };
  yoga: { number: number; name: string };
  karana: { number: number; name: string; type: "fixed" | "recurring" };
  masa: { number: number; name: string };
  ritu: { number: number; name: string };
  samvatsara: { number: number; name: string };
  sun_longitude: number;
  moon_longitude: number;
  ayanamsha: number;
  summary: string;
}

export function Panchanga() {
  const [date, setDate] = useState<DateValue>(currentDateTimeValue);
  const [result, setResult] = useState<PanchangaResult | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setResult(null);
    setError(null);
    api
      .panchanga(date)
      .then((r) => {
        if (cancelled) return;
        setResult(r as PanchangaResult);
        setError(null);
      })
      .catch(reason => { if (!cancelled) setError(reason); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [date.year, date.month, date.day, date.utc_offset]);

  return (
    <div>
      <PageHeader title="Panchanga" subtitle="Tithi, vara, nakshatra, yoga, karana, masa, ritu, samvatsara" />
      <DateInput value={date} onChange={setDate} withZone withTime />
      {loading && <p role="status">Calculating Panchanga…</p>}
      <ErrorBox error={error} />
      {result && (
        <KVTable
          title={`Panchanga — ${result.at}`}
          rows={[
            ["Tithi", `${result.tithi.name} (${result.tithi.paksha} paksha) — #${result.tithi.number} (${(result.tithi.fraction * 100).toFixed(1)}% elapsed)`],
            ["Vara", result.vara.name],
            ["Nakshatra", `${result.nakshatra.name} (pada ${result.nakshatra.pada})`],
            ["Yoga", result.yoga.name],
            ["Karana", result.karana.name],
            ["Masa", result.masa.name],
            ["Ritu", result.ritu.name],
            ["Samvatsara", result.samvatsara.name],
            ["Sun longitude", `${result.sun_longitude.toFixed(3)}°`],
            ["Moon longitude", `${result.moon_longitude.toFixed(3)}°`],
            ["Ayanamsha", `${result.ayanamsha.toFixed(3)}°`],
          ]}
        />
      )}
    </div>
  );
}
