/** A calendar date with a fractional day, as the book payloads carry one. */
export interface DayDate {
  year: number;
  month: number;
  day: number;
}

/** Preserve a lesson's date when opening its source calculation. */
export function bookDateFromSearch(search: string, fallback: DayDate): DayDate {
  const params = new URLSearchParams(search);
  if (!["year", "month", "day"].every(key => params.has(key))) return fallback;
  const year = Number(params.get("year"));
  const month = Number(params.get("month"));
  const day = Number(params.get("day"));
  if (![year, month, day].every(Number.isInteger) || year < 1599 || year > 2601) return fallback;
  const date = new Date(Date.UTC(year, month - 1, day));
  if (date.getUTCFullYear() !== year || date.getUTCMonth() + 1 !== month || date.getUTCDate() !== day) return fallback;
  return { year, month, day };
}

/**
 * "2024-02-11, 08:23 Ujjain mean time" from a fractional day; the time of day
 * is the fraction. Book payloads reckon in Ujjain mean time (UTC+5:03), as the
 * text does from the meridian of Lanka.
 */
export function fmtDate(d: DayDate): string {
  const whole = Math.floor(d.day);
  const minutes = Math.round((d.day - whole) * 1440);
  const hh = String(Math.floor(minutes / 60) % 24).padStart(2, "0");
  const mm = String(minutes % 60).padStart(2, "0");
  return `${d.year}-${String(d.month).padStart(2, "0")}-${String(whole).padStart(2, "0")}, ${hh}:${mm} Ujjain mean time`;
}
