/** A calendar date with a fractional day, as the book payloads carry one. */
export interface DayDate {
  year: number;
  month: number;
  day: number;
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
