import { useEffect, useState } from "react";
import { api } from "../api";
import { DateInput, DateValue, DEFAULT_LATLON, LatLon, LatLonInput, todayValue } from "../components/Inputs";
import { ErrorBox, KVTable, PageHeader } from "../components/Tables";

interface MoonResult {
  phase: {
    illuminated_percent: number; phase_name: string; is_waxing: boolean;
    elongation_deg: number; crescent_width_arcmin: number; bright_limb_angle_deg: number;
  };
  horn: { horn_angle_deg: number };
  rise_set: { moonrise_time?: string; moonset_time?: string; zone: string; summary: string };
}

export function Moon() {
  const [date, setDate] = useState<DateValue>(todayValue());
  const [latlon, setLatlon] = useState<LatLon>(DEFAULT_LATLON);
  const [result, setResult] = useState<MoonResult | null>(null);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    api
      .moon({ ...date, ...latlon })
      .then((r) => {
        setResult(r as MoonResult);
        setError(null);
      })
      .catch(setError);
  }, [date.year, date.month, date.day, latlon.latitude, latlon.longitude]);

  return (
    <div>
      <PageHeader title="Moon" subtitle="Phase, crescent width (bahu) and horn tilt (valana) (Ch.10)" />
      <DateInput value={date} onChange={setDate} withZone />
      <LatLonInput value={latlon} onChange={setLatlon} />
      <ErrorBox error={error} />
      {result && (
        <KVTable
          rows={[
            ["Phase", `${result.phase.phase_name} (${result.phase.is_waxing ? "Waxing" : "Waning"})`],
            ["Illumination", `${result.phase.illuminated_percent.toFixed(1)}%`],
            ["Elongation", `${result.phase.elongation_deg.toFixed(2)}°`],
            ["Crescent width (bahu)", `${result.phase.crescent_width_arcmin.toFixed(2)}′`],
            ["Bright limb angle", `${result.phase.bright_limb_angle_deg.toFixed(2)}°`],
            ["Horn tilt (valana)", `${result.horn.horn_angle_deg.toFixed(2)}°`],
            ["Moonrise", result.rise_set.moonrise_time ? `${result.rise_set.moonrise_time} (${result.rise_set.zone})` : "—"],
            ["Moonset", result.rise_set.moonset_time ? `${result.rise_set.moonset_time} (${result.rise_set.zone})` : "—"],
          ]}
        />
      )}
    </div>
  );
}
