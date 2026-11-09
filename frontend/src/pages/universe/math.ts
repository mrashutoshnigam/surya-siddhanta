import type { Model, Positions, Sample, Vector } from "./types";

export const MIN_TIME = Date.parse("1550-01-01T00:00:00Z") / 1000;
export const MAX_TIME = Date.parse("2649-12-31T23:59:59.999Z") / 1000;
export const DAY = 86400;
export const HISTORICAL_ORDER = ["Earth", "Moon", "Mercury", "Venus", "Sun", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu"];
export const MODERN_ORDER = ["Sun", "Mercury", "Venus", "Earth", "Moon", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune"];

export function sampleAt(samples: Sample[], timestamp: number): Positions | null {
  if (!samples.length || timestamp < samples[0].timestamp || timestamp > samples[samples.length - 1].timestamp) return null;
  let low = 0, high = samples.length - 1;
  while (high - low > 1) {
    const mid = (low + high) >> 1;
    if (samples[mid].timestamp > timestamp) high = mid; else low = mid;
  }
  const a = samples[low], b = samples[high];
  if (a === b) return a.positions;
  const seconds = b.timestamp - a.timestamp, u = (timestamp - a.timestamp) / seconds, dt = seconds / DAY;
  const h = [2*u**3-3*u*u+1, u**3-2*u*u+u, -2*u**3+3*u*u, u**3-u*u];
  return Object.fromEntries(Object.entries(a.positions).map(([body, p]) => [body, p.map((v, i) =>
    h[0]*v + h[1]*dt*a.velocities[body][i] + h[2]*b.positions[body][i] + h[3]*dt*b.velocities[body][i]) as Vector]));
}

/** Keep direction; deliberately compress radii independently of globe sizes. */
export function scenePosition(body: string, positions: Positions, model: Model): Vector {
  const p = positions[body];
  if (!p) return [0, 0, 0];
  let q = p, radius: number;
  if (model === "modern" && body === "Moon" && positions.Earth) {
    q = p.map((v, i) => v - positions.Earth[i]) as Vector;
    const earth = scenePosition("Earth", positions, model), size = Math.hypot(...q) || 1;
    return [earth[0] + q[0]/size*1.55, earth[1] + q[2]/size*1.55, earth[2] - q[1]/size*1.55];
  }
  if (model === "historical") {
    const rank = {Earth:0,Moon:1,Mercury:2,Venus:3,Sun:4,Mars:5,Jupiter:6,Saturn:7,Rahu:1,Ketu:1}[body] ?? 0;
    radius = rank === 0 ? 0 : 2 + rank * 2.1;
  } else {
    const au = Math.hypot(...q) / 149597870.7;
    radius = au ? 2.8 + 5.5 * Math.log2(1 + au) : 0;
  }
  if (radius === 0) return [0, 0, 0];
  const size = Math.hypot(...q) || 1;
  return [q[0]/size*radius, q[2]/size*radius, -q[1]/size*radius];
}

export function formatClock(timestamp: number, offset: number): string {
  return new Date((timestamp + offset * 3600) * 1000).toISOString().slice(0, 16);
}

export function parseClock(value: string, offset: number): number | null {
  if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(value)) return null;
  const ms = Date.parse(value + "Z");
  if (!Number.isFinite(ms) || new Date(ms).toISOString().slice(0, 16) !== value) return null;
  const time = ms / 1000 - offset * 3600;
  return time >= MIN_TIME && time <= MAX_TIME ? time : null;
}

export const angularDifference = (a: number, b: number) => ((b - a + 540) % 360) - 180;
export const modelLabel = (model: Model) => model === "historical" ? "Surya Siddhanta" : "Modern astronomy";
export const iso = (timestamp: number) => new Date(timestamp * 1000).toISOString();
export const globeSize = (body: string) => ({Sun:1.15,Earth:.57,Moon:.25,Mercury:.33,Venus:.53,Mars:.43,Jupiter:.96,Saturn:.82,Uranus:.65,Neptune:.64,Rahu:.13,Ketu:.13}[body] ?? .5);
