// Thin fetch wrapper around the FastAPI backend (proxied at /api by Vite in dev).

import type { GlossaryDoc } from "./glossary/types";

const BASE = "/api";

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `${res.status} ${res.statusText}`);
  }
  return res.json();
}

async function get<T>(path: string, params?: Record<string, string | number>): Promise<T> {
  const qs = params
    ? "?" + new URLSearchParams(Object.fromEntries(Object.entries(params).map(([k, v]) => [k, String(v)])))
    : "";
  const res = await fetch(`${BASE}${path}${qs}`);
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `${res.status} ${res.statusText}`);
  }
  return res.json();
}

export interface DateInput {
  year: number;
  month: number;
  day: number;
  /** Zone of the clock time, hours from UTC; the server reads IST (5.5) when absent. */
  utc_offset?: number;
}

export interface DateLocationInput extends DateInput {
  latitude: number;
  longitude: number;
}

export const DEFAULT_LAT = 23.18;
export const DEFAULT_LON = 75.78;

export const api = {
  planetPosition: (body: DateInput & { planet: string }) => post("/calc/planet-position", body),
  allPlanets: (body: DateInput & { planets?: string[] }) => post("/calc/all-planets", body),
  panchanga: (body: DateInput) => post("/calc/panchanga", body),
  lunarEclipse: (body: DateInput) => post("/calc/eclipse/lunar", body),
  solarEclipse: (body: DateLocationInput) => post("/calc/eclipse/solar", body),
  conjunctions: (body: { planet1: string; planet2: string; year: number; month?: number; months?: number }) =>
    post("/calc/conjunctions", body),
  stars: (body: DateLocationInput & { nakshatra: string }) => post("/calc/stars", body),
  heliacal: (body: { planet: string; year: number; months?: number }) => post("/calc/heliacal", body),
  moon: (body: DateLocationInput) => post("/calc/moon", body),
  patas: (body: DateInput & { days?: number }) => post("/calc/patas", body),
  pataActive: (body: DateInput & { hour?: number }) => post("/calc/pata/active", body),
  cosmographyEarth: (body: { latitude: number; longitude: number }) =>
    post("/calc/cosmography/earth", body),
  cosmographyOrbits: (body: { body?: string }) => post("/calc/cosmography/orbits", body),
  cosmographyTime: (body: DateInput) => post("/calc/cosmography/time", body),
  cosmographyWorlds: (body: { section?: string }) => post("/calc/cosmography/worlds", body),
  instrumentsSphere: (
    body: DateLocationInput & { hour: number; include_stars?: boolean },
  ) => post("/calc/instruments/sphere", body),
  instrumentsClepsydra: (body: {
    sinkings?: number;
    ghatis?: number;
    partial?: number;
    year?: number;
    month?: number;
    day?: number;
    latitude?: number;
    observed_per_day?: number;
  }) => post("/calc/instruments/clepsydra", body),
  instrumentsTime: (
    body: DateInput & {
      instrument: "nara" | "cakra" | "dhanus" | "yashti";
      value: number;
      latitude: number;
      gnomon?: number;
      forenoon?: boolean;
      staff_length?: number;
    },
  ) => post("/calc/instruments/time", body),
  instrumentsCatalog: (body: { section?: string }) => post("/calc/instruments/catalog", body),
  placeTime: (body: DateLocationInput & { gnomon_altitude?: number }) => post("/calc/place-time", body),
  aharganaVerse: (body: { years: number; months?: number; tithis?: number; from_creation?: boolean }) =>
    post("/calc/ahargana-verse", body),
  dailyPanchanga: (body: DateInput) => post("/calc/daily-panchanga", body),
  dailyPanchangaRange: (body: DateInput & { days?: number }) => post("/calc/daily-panchanga/range", body),

  bookChapter1: (body: DateInput) => post("/book/chapter/1", body),
  bookChapter2: (body: DateInput & { latitude?: number }) => post("/book/chapter/2", body),
  bookChapter2Probe: (body: Record<string, unknown>) => post("/book/chapter/2/probe", body),
  bookChapter3: (body: DateInput & { latitude?: number }) => post("/book/chapter/3", body),
  bookChapter3Probe: (body: Record<string, unknown>) => post("/book/chapter/3/probe", body),
  bookChapter4: (body: DateInput) => post("/book/chapter/4", body),
  bookChapter4Probe: (body: Record<string, unknown>) => post("/book/chapter/4/probe", body),
  bookChapter5: (body: DateInput & { latitude?: number; longitude?: number }) => post("/book/chapter/5", body),
  bookChapter5Probe: (body: Record<string, unknown>) => post("/book/chapter/5/probe", body),
  bookChapter6: (body: DateInput & { kind: string; latitude?: number; longitude?: number }) => post("/book/chapter/6", body),
  bookChapter6Probe: (body: Record<string, unknown>) => post("/book/chapter/6/probe", body),
  bookChapter7: (body: DateInput & { planet1: string; planet2: string; search_days?: number }) => post("/book/chapter/7", body),
  bookChapter8: (body: DateInput & { star: string; planet: string; months?: number; latitude?: number; longitude?: number }) => post("/book/chapter/8", body),
  bookChapter9: (body: DateInput & { planet: string; months?: number }) => post("/book/chapter/9", body),
  bookChapter10: (body: DateInput & { latitude?: number; longitude?: number }) => post("/book/chapter/10", body),
  bookChapter11: (body: DateInput & { days?: number }) => post("/book/chapter/11", body),
  bookChapter12: (body: DateInput & { latitude?: number; longitude?: number }) => post("/book/chapter/12", body),
  bookChapter13: (body: DateInput & { latitude?: number; longitude?: number; shadow?: number; forenoon?: boolean }) => post("/book/chapter/13", body),
  bookChapter14: (body: DateInput & { value?: number; from_mana?: string; to_mana?: string; heliacal?: boolean }) => post("/book/chapter/14", body),

  corpusChapters: () => get("/corpus/chapters"),
  corpusVerse: (chapter: number, verse: number) => get(`/corpus/verse/${chapter}/${verse}`),
  corpusVerses: (chapter: number) => get(`/corpus/verses/${chapter}`),
  corpusSearch: (q: string, limit = 8) => get("/corpus/search", { q, limit }),

  glossary: () => get<GlossaryDoc>("/glossary"),

  chat: (body: { message: string; session_id?: string }) => post("/chat", body),
  chatReset: (sessionId: string) => post(`/chat/${sessionId}/reset`, {}),
};

/** URL of a glossary diagram, from the file name stored in the term's `image.src`. */
export function glossaryImageUrl(src: string): string {
  return `${BASE}/glossary/img/${encodeURIComponent(src)}`;
}
