import { useEffect, useState } from "react";
import { api } from "../api";
import { DateInput, DateValue, todayValue } from "../components/Inputs";
import { ErrorBox, GridTable, KVTable, PageHeader } from "../components/Tables";

// The daily_panchanga core module returns a fairly open-ended dict (base
// panchanga fields plus moon phase / rashi metadata); typed loosely here
// rather than mirroring every field.
type Panchanga = Record<string, any>;

export function DailyPanchanga() {
  const [date, setDate] = useState<DateValue>(todayValue());
  const [days, setDays] = useState(7);
  const [today, setToday] = useState<Panchanga | null>(null);
  const [range, setRange] = useState<Panchanga[] | null>(null);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    Promise.all([
      api.dailyPanchanga(date),
      api.dailyPanchangaRange({ ...date, days }),
    ])
      .then(([single, rangeResult]) => {
        setToday(single as Panchanga);
        setRange((rangeResult as { days: Panchanga[] }).days);
        setError(null);
      })
      .catch(setError);
  }, [date.year, date.month, date.day, days]);

  return (
    <div>
      <PageHeader title="Daily Panchanga" subtitle="Five-element almanac for a single day or a short range" />
      <DateInput value={date} onChange={setDate} />
      <div className="field-row">
        <label>
          Range (days)
          <input type="number" value={days} min={1} max={30} onChange={(e) => setDays(Number(e.target.value))} />
        </label>
      </div>
      <ErrorBox error={error} />
      {today && (
        <KVTable
          title={`Panchanga — ${today.date}`}
          rows={[
            ["Tithi", `${today.tithi?.name ?? "#" + today.tithi?.number} (${today.tithi?.paksha ?? ""})`],
            ["Vara", `${today.vara?.name} (${today.vara?.name_en ?? ""})`],
            ["Nakshatra", `${today.nakshatra?.name} pada ${today.nakshatra?.pada}`],
            ["Yoga", today.yoga?.name ?? `#${today.yoga?.number}`],
            ["Karana", today.karana?.name ?? `#${today.karana?.number}`],
            ["Masa", today.masa?.name],
            ["Ritu", today.ritu?.name],
            ["Samvatsara", today.samvatsara?.name],
            ["Moon phase", today.moon_phase ? `${today.moon_phase.name} (${today.moon_phase.illumination_pct}%)` : "—"],
            ["Sun rashi", today.sun_rashi ? `${today.sun_rashi.symbol} ${today.sun_rashi.name}` : "—"],
            ["Moon rashi", today.moon_rashi ? `${today.moon_rashi.symbol} ${today.moon_rashi.name}` : "—"],
          ]}
        />
      )}
      {range && (
        <GridTable
          headers={["Date", "Tithi", "Vara", "Nakshatra", "Yoga", "Masa", "Ritu"]}
          rows={range.map((d) => [
            d.date,
            d.tithi?.name ?? d.tithi?.number,
            d.vara?.name,
            d.nakshatra?.name,
            d.yoga?.name ?? d.yoga?.number,
            d.masa?.name,
            d.ritu?.name,
          ])}
        />
      )}
    </div>
  );
}
