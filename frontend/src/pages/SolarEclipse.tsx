import { useEffect, useState } from "react";
import { api } from "../api";
import { DateInput, DateValue, DEFAULT_LATLON, LatLon, LatLonInput } from "../components/Inputs";
import { ErrorBox, KVTable, PageHeader } from "../components/Tables";

interface SolarEclipseResult {
  is_eclipse: boolean;
  eclipse_type: string;
  magnitude: number;
  sun_diameter_arcmin: number;
  moon_diameter_arcmin: number;
  lambana_arcmin: number | null;
  nati_arcmin: number | null;
  half_duration_min: number | null;
  locally_visible?: boolean;
  sun_altitude_deg?: number;
  notes: string;
  summary: string;
}

export function SolarEclipse() {
  const [date, setDate] = useState<DateValue>({ year: new Date().getFullYear(), month: 4, day: 1 });
  const [latlon, setLatlon] = useState<LatLon>(DEFAULT_LATLON);
  const [result, setResult] = useState<SolarEclipseResult | null>(null);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    api
      .solarEclipse({ ...date, ...latlon })
      .then((r) => {
        setResult(r as SolarEclipseResult);
        setError(null);
      })
      .catch(setError);
  }, [date.year, date.month, date.day, latlon.latitude, latlon.longitude]);

  return (
    <div>
      <PageHeader
        title="Solar Eclipse"
        subtitle="Predicted with the Surya Siddhanta method (Ch.5), topocentric. Use a day near new moon."
      />
      <DateInput value={date} onChange={setDate} />
      <LatLonInput value={latlon} onChange={setLatlon} />
      <ErrorBox error={error} />
      {result && (
        <KVTable
          rows={[
            ["Eclipse?", result.is_eclipse ? `Yes — ${result.eclipse_type}` : "No"],
            ["Magnitude", result.magnitude.toFixed(3)],
            ["Sun diameter", `${result.sun_diameter_arcmin.toFixed(1)}'`],
            ["Moon diameter", `${result.moon_diameter_arcmin.toFixed(1)}'`],
            ["Lambana (parallax)", result.lambana_arcmin != null ? `${result.lambana_arcmin.toFixed(1)}'` : "—"],
            ["Nati (parallax)", result.nati_arcmin != null ? `${result.nati_arcmin.toFixed(1)}'` : "—"],
            ["Half-duration", result.half_duration_min != null ? `${result.half_duration_min.toFixed(1)} min` : "—"],
            ["Sun's altitude at conjunction", result.sun_altitude_deg != null ? `${result.sun_altitude_deg.toFixed(1)}°` : "—"],
            [
              "Visible from this place",
              result.locally_visible == null
                ? "—"
                : result.locally_visible
                  ? "Yes"
                  : result.is_eclipse
                    ? "No — Sun below the horizon"
                    : "No",
            ],
            ["Summary", result.summary],
          ]}
        />
      )}
    </div>
  );
}
