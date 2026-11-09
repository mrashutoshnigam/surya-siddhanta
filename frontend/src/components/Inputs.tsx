import { DEFAULT_LAT, DEFAULT_LON } from "../api";

export interface DateValue {
  year: number;
  month: number;
  day: number;
  /** Zone of the clock time, hours from UTC; the API reads IST (5.5) when absent. */
  utc_offset?: number;
}

/** The zone the API assumes when a request carries no utc_offset: IST. */
export const DEFAULT_UTC_OFFSET = 5.5;

export function DateInput({
  value,
  onChange,
  minYear = -3000,
  maxYear = 4000,
  withZone = false,
  withTime = false,
  dayStep = 0.01,
}: {
  value: DateValue;
  onChange: (v: DateValue) => void;
  minYear?: number;
  maxYear?: number;
  /** Show a time-zone field: for pages where the time of day matters. */
  withZone?: boolean;
  /** Show clock time separately while keeping fractional days in API requests. */
  withTime?: boolean;
  /** Whole-day lessons can opt into integer stepping without changing other pages. */
  dayStep?: number;
}) {
  const wholeDay = Math.floor(value.day);
  const minuteOfDay = Math.min(1439, Math.round((value.day - wholeDay) * 1440));
  const clock = `${String(Math.floor(minuteOfDay / 60)).padStart(2, "0")}:${String(minuteOfDay % 60).padStart(2, "0")}`;
  return (
    <div className="field-row">
      <label>
        Year (CE)
        <input
          type="number"
          value={value.year}
          min={minYear}
          max={maxYear}
          onChange={(e) => onChange({ ...value, year: Number(e.target.value) })}
        />
      </label>
      <label>
        Month
        <input
          type="number"
          value={value.month}
          min={1}
          max={12}
          onChange={(e) => onChange({ ...value, month: Number(e.target.value) })}
        />
      </label>
      <label>
        {withZone && !withTime ? "Day (fraction = time of day)" : "Day"}
        <input
          type="number"
          value={withTime ? wholeDay : value.day}
          min={1}
          max={31}
          step={withTime ? 1 : dayStep}
          onChange={(e) => onChange({ ...value, day: Number(e.target.value) + (withTime ? minuteOfDay / 1440 : 0) })}
        />
      </label>
      {withTime && (
        <label>
          Time
          <input
            type="time"
            value={clock}
            step={60}
            onChange={event => {
              if (!event.target.value) return;
              const [hours, minutes] = event.target.value.split(":").map(Number);
              onChange({ ...value, day: wholeDay + (hours * 60 + minutes) / 1440 });
            }}
          />
        </label>
      )}
      {withZone && (
        <label>
          Time zone (hours from UTC; IST = 5.5)
          <input
            type="number"
            value={value.utc_offset ?? DEFAULT_UTC_OFFSET}
            min={-12}
            max={14}
            step={0.25}
            onChange={(e) => onChange({ ...value, utc_offset: Number(e.target.value) })}
          />
        </label>
      )}
      {withTime && <button type="button" onClick={() => onChange(currentDateTimeValue())}>Now</button>}
    </div>
  );
}

export interface LatLon {
  latitude: number;
  longitude: number;
}

export function LatLonInput({ value, onChange }: { value: LatLon; onChange: (v: LatLon) => void }) {
  return (
    <div className="field-row">
      <label>
        Latitude (°N)
        <input
          type="number"
          value={value.latitude}
          step={0.01}
          min={-90}
          max={90}
          onChange={(e) => onChange({ ...value, latitude: Number(e.target.value) })}
        />
      </label>
      <label>
        Longitude (°E)
        <input
          type="number"
          value={value.longitude}
          step={0.01}
          min={-180}
          max={180}
          onChange={(e) => onChange({ ...value, longitude: Number(e.target.value) })}
        />
      </label>
    </div>
  );
}

export const DEFAULT_LATLON: LatLon = { latitude: DEFAULT_LAT, longitude: DEFAULT_LON };

export function todayValue(): DateValue {
  const d = new Date();
  return { year: d.getFullYear(), month: d.getMonth() + 1, day: d.getDate() };
}

/** Current browser-local date and clock minute, with an explicit UTC offset. */
export function currentDateTimeValue(): DateValue {
  const now = new Date();
  return {
    year: now.getFullYear(),
    month: now.getMonth() + 1,
    day: now.getDate() + (now.getHours() * 60 + now.getMinutes()) / 1440,
    utc_offset: -now.getTimezoneOffset() / 60,
  };
}
