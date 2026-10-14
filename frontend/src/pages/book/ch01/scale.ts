// Ratio arithmetic for the sliders.
//
// Nothing here re-derives any astronomy. Every function takes constants the
// backend shipped in the card payload -- a unit's length in seconds, a
// revolution count, the civil days in an Age -- and scales them, so the
// figures a slider shows are the same figures ch01_mean_motions.py would
// give for the same inputs. Anything that needs more than a ratio (the
// i.48-51 integer chain, which overflows a double) asks the server instead.

/** Convert an amount from one unit to another, given their lengths in seconds. */
export function convertUnits(
  amount: number,
  fromSeconds: number,
  toSeconds: number,
): number {
  return (amount * fromSeconds) / toSeconds;
}

/** Normalize an angle to [0, 360). */
export function norm360(degrees: number): number {
  return ((degrees % 360) + 360) % 360;
}

/**
 * Mean longitude by the v.35 proportion, for an arbitrary ahargana.
 *
 * `epoch` is where the body stood at the Kali epoch and `retrograde`
 * reverses the motion, exactly as `mean_longitude` applies them to the
 * Moon's apsis (90°) and node (180°, backwards).
 */
export function meanLongitude(
  bhagana: number,
  ahargana: number,
  civilDaysPerMahayuga: number,
  epoch = 0,
  retrograde = false,
): number {
  const travelled = ((bhagana * ahargana) / civilDaysPerMahayuga) * 360;
  return norm360(retrograde ? epoch - travelled : epoch + travelled);
}

/** Format degrees as `d° mm' ss.ss"`, matching api/book.py's `_dms`. */
export function dms(degrees: number): string {
  const deg = norm360(degrees);
  const d = Math.floor(deg);
  const minutesTotal = (deg - d) * 60;
  const m = Math.floor(minutesTotal);
  const s = (minutesTotal - m) * 60;
  return `${d}° ${String(m).padStart(2, "0")}' ${s.toFixed(2).padStart(5, "0")}"`;
}

/** Sign and degrees within it, given the twelve rashi names. */
export function rashiOf(degrees: number, rashis: string[]): string {
  const deg = norm360(degrees);
  const index = Math.floor(deg / 30);
  return `${rashis[index]} ${(deg - index * 30).toFixed(2)}°`;
}

/** Thousands separators, for the very large counts this chapter deals in. */
export function grouped(value: number, fractionDigits = 0): string {
  return value.toLocaleString("en-US", {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  });
}

/**
 * A readable length of time from a count of seconds.
 *
 * Used by the unit converter to say what an amount comes to in ordinary
 * terms; it says nothing the SS says, and is presentation only.
 */
export function humanSeconds(seconds: number): string {
  const abs = Math.abs(seconds);
  if (abs < 1e-3) return `${(seconds * 1e6).toFixed(2)} µs`;
  if (abs < 1) return `${(seconds * 1e3).toFixed(3)} ms`;
  if (abs < 60) return `${seconds.toFixed(3)} s`;
  if (abs < 3600) return `${(seconds / 60).toFixed(3)} min`;
  if (abs < 86400) return `${(seconds / 3600).toFixed(3)} h`;
  if (abs < 86400 * 365.25) return `${(seconds / 86400).toFixed(3)} days`;
  return `${(seconds / (86400 * 365.2587565)).toFixed(4)} sidereal years`;
}

/**
 * A number at a readable precision, whatever its magnitude.
 *
 * This chapter deals in figures from a truti (3 × 10⁻⁵ s) to the civil
 * days of an Aeon (1.6 × 10¹²), so no single format serves.
 */
export function fmt(value: number): string {
  const abs = Math.abs(value);
  if (value === 0) return "0";
  if (abs >= 1e15 || abs < 1e-4) return value.toExponential(4);
  if (abs >= 1000) return grouped(value, 0);
  if (abs >= 1) return String(Number(value.toFixed(4)));
  return String(Number(value.toPrecision(5)));
}
