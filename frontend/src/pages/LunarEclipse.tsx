import { useEffect, useState } from "react";
import { api } from "../api";
import { DateInput, DateValue } from "../components/Inputs";
import { ErrorBox, KVTable, PageHeader } from "../components/Tables";

interface LunarEclipseResult {
  is_eclipse: boolean;
  eclipse_type: string;
  magnitude: number;
  moon_latitude_arcmin: number;
  moon_diameter_arcmin: number;
  shadow_diameter_arcmin: number;
  half_duration_min: number | null;
  totality_half_min: number | null;
  notes: string;
  summary: string;
}

export function LunarEclipse() {
  const [date, setDate] = useState<DateValue>({ year: new Date().getFullYear(), month: 4, day: 15 });
  const [result, setResult] = useState<LunarEclipseResult | null>(null);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    api
      .lunarEclipse(date)
      .then((r) => {
        setResult(r as LunarEclipseResult);
        setError(null);
      })
      .catch(setError);
  }, [date.year, date.month, date.day]);

  return (
    <div>
      <PageHeader title="Lunar Eclipse" subtitle="Predicted with the Surya Siddhanta method (Ch.4). Use a day near full moon." />
      <DateInput value={date} onChange={setDate} />
      <ErrorBox error={error} />
      {result && (
        <KVTable
          rows={[
            ["Eclipse?", result.is_eclipse ? `Yes — ${result.eclipse_type}` : "No"],
            ["Magnitude", result.magnitude.toFixed(3)],
            ["Moon latitude", `${result.moon_latitude_arcmin.toFixed(1)}'`],
            ["Moon diameter", `${result.moon_diameter_arcmin.toFixed(1)}'`],
            ["Shadow diameter", `${result.shadow_diameter_arcmin.toFixed(1)}'`],
            ["Half-duration", result.half_duration_min != null ? `${result.half_duration_min.toFixed(1)} min` : "—"],
            ["Totality half", result.totality_half_min != null ? `${result.totality_half_min.toFixed(1)} min` : "—"],
            ["Summary", result.summary],
          ]}
        />
      )}
    </div>
  );
}
