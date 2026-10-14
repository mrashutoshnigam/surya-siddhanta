import { useEffect, useState } from "react";
import { api } from "../api";
import { DateInput, DateValue, todayValue } from "../components/Inputs";
import { ErrorBox, KVTable, PageHeader } from "../components/Tables";

interface PanchangaResult {
  tithi: { number: number; fraction: number };
  vara: { number: number; name: string };
  nakshatra: { number: number; name: string; pada: number };
  yoga: { number: number };
  karana: { number: number };
  masa: { number: number; name: string };
  ritu: { number: number; name: string };
  samvatsara: { number: number; name: string };
  sun_longitude: number;
  moon_longitude: number;
  ayanamsha: number;
  summary: string;
}

export function Panchanga() {
  const [date, setDate] = useState<DateValue>(todayValue());
  const [result, setResult] = useState<PanchangaResult | null>(null);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    api
      .panchanga(date)
      .then((r) => {
        setResult(r as PanchangaResult);
        setError(null);
      })
      .catch(setError);
  }, [date.year, date.month, date.day]);

  return (
    <div>
      <PageHeader title="Panchanga" subtitle="Tithi, vara, nakshatra, yoga, karana, masa, ritu, samvatsara" />
      <DateInput value={date} onChange={setDate} withZone />
      <ErrorBox error={error} />
      {result && (
        <KVTable
          title={`Panchanga — ${date.year}-${String(date.month).padStart(2, "0")}-${String(date.day).padStart(2, "0")}`}
          rows={[
            ["Tithi", `#${result.tithi.number} (${(result.tithi.fraction * 100).toFixed(1)}% elapsed)`],
            ["Vara", result.vara.name],
            ["Nakshatra", `${result.nakshatra.name} (pada ${result.nakshatra.pada})`],
            ["Yoga", `#${result.yoga.number}`],
            ["Karana", `#${result.karana.number}`],
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
