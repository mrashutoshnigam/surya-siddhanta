import { useEffect, useState } from "react";
import { api } from "../api";
import { DateInput, LatLonInput, DEFAULT_LATLON, todayValue } from "../components/Inputs";
import type { DateValue, LatLon } from "../components/Inputs";
import { ErrorBox, GridTable, KVTable, PageHeader } from "../components/Tables";

// Chapter 12 states the fixed dimensions of the world rather than anything
// that varies with time, so three of the four tabs take no date at all. The
// tabs mirror the four clusters of the chapter and the four /calc/cosmography
// routes one for one.
const TABS = ["Earth & Place", "Orbits & Distances", "Cosmic Time", "Worlds"] as const;
type Tab = (typeof TABS)[number];

interface SphereAspect {
  kind: string;
  pole_altitude: number;
  colatitude: number;
  hemisphere: string;
  day_ghatis: number | null;
  description: string;
}

interface LatitudeLimit {
  latitude: number;
  declination?: number;
  yojanas_from_equator: number;
  signs_invisible?: number;
  verse: string;
}

interface EarthResult {
  earth_diameter_yojanas: number;
  earth_circumference_yojanas: number;
  corrected_circumference_yojanas: number;
  desantara: {
    yojanas: number;
    ghatis: number;
    corrections_arcmin: Record<string, number>;
    note: string;
  };
  sphere_aspect: SphereAspect;
  polar_day_limit: LatitudeLimit & { obliquity: number };
  invisibility_limits: LatitudeLimit[];
  solar_overhead_band: { yojanas: number; degrees: number };
  summary: string;
}

interface Orbit {
  body: string;
  orbit_yojanas: number;
  revolutions_per_kalpa: number;
  orbit_diameter_yojanas: number;
  distance_yojanas: number;
  daily_motion_arcmin: number;
  stated_yojanas: number | null;
  stated_difference: number | null;
  verse: string | null;
}

interface OrbitsResult {
  daily_linear_motion_yojanas: number;
  ether_orbit_yojanas: number;
  moon_orbit_yojanas: number;
  orbits: Orbit[];
  order_outward: string[];
  summary: string;
}

interface TimeResult {
  day_lengths_in_days: Record<string, number>;
  brahma_day: {
    years_elapsed: number;
    years_remaining: number;
    fraction_elapsed: number;
    kalpa_years: number;
  };
  regents: { day: string; month: string; year: string; horas: string[]; order: string[] };
  day_and_night: { beings: string; station: string; day: string; night: string; verse: string }[];
  summary: string;
}

interface WorldsResult {
  chapter_name_en: string;
  note: string;
  inquiries: { number: number; question: string; verse: string; answered_in: string }[];
  creation_sequence: { order: number; agent: string; act: string; verse: string }[];
  elements: { order: number; name: string; iast: string; qualities: number; verse: string }[];
  planet_origins: { planet: string; origin: string; verse: string }[];
  patalas: { count: number; named_in_text: boolean; description: string; verse: string };
  reference_places: {
    name: string;
    iast: string;
    latitude: number;
    longitude: number | null;
    clime: string | null;
    direction: string;
    note: string;
    verse: string;
  }[];
  orbital_order: { rank: number; name: string; iast: string; kind: string }[];
  cities_clock_at_yamakoti_noon: Record<string, number>;
  summary: string;
}

/** Format a yojana count with thousands separators; the orbits run to sixteen digits. */
function yojanas(value: number, digits = 0): string {
  return value.toLocaleString(undefined, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

/** Turn a decimal local hour into HH:MM, for the four-cities clock of v.70. */
function clockTime(hour: number): string {
  const h = Math.floor(hour);
  const m = Math.round((hour - h) * 60);
  return `${String(h % 24).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
}

export function Cosmography() {
  const [tab, setTab] = useState<Tab>("Earth & Place");
  const [place, setPlace] = useState<LatLon>(DEFAULT_LATLON);
  const [date, setDate] = useState<DateValue>(todayValue());

  const [earth, setEarth] = useState<EarthResult | null>(null);
  const [orbits, setOrbits] = useState<OrbitsResult | null>(null);
  const [time, setTime] = useState<TimeResult | null>(null);
  const [worlds, setWorlds] = useState<WorldsResult | null>(null);

  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);

  function run<T>(call: Promise<unknown>, set: (value: T) => void) {
    setLoading(true);
    call
      .then((r) => {
        set(r as T);
        setError(null);
      })
      .catch(setError)
      .finally(() => setLoading(false));
  }

  const loadEarth = () => run<EarthResult>(api.cosmographyEarth(place), setEarth);
  const loadTime = () => run<TimeResult>(api.cosmographyTime(date), setTime);

  // The orbits and the worlds take no input at all, so they are fetched once
  // when their tab is first opened rather than behind a button.
  useEffect(() => {
    if (tab === "Orbits & Distances" && !orbits) {
      run<OrbitsResult>(api.cosmographyOrbits({}), setOrbits);
    }
    if (tab === "Worlds" && !worlds) {
      run<WorldsResult>(api.cosmographyWorlds({}), setWorlds);
    }
  }, [tab, orbits, worlds]);

  return (
    <div>
      <PageHeader
        title="Cosmography"
        subtitle="The earth, the orbits of the planets in yojanas, the days of gods and of Brahma, and the creation — Bhugoladhikara (Ch.12)"
      />

      <div className="ss-tabs">
        {TABS.map((name) => (
          <button
            key={name}
            className={"ss-tab" + (tab === name ? " active" : "")}
            onClick={() => setTab(name)}
          >
            {name}
          </button>
        ))}
      </div>

      <ErrorBox error={error} />

      {tab === "Earth & Place" && (
        <>
          <LatLonInput value={place} onChange={setPlace} />
          <div className="field-row">
            <button onClick={loadEarth} disabled={loading}>
              {loading ? "Computing…" : "Compute"}
            </button>
          </div>
          {earth && (
            <>
              <p className="ss-note">{earth.summary}</p>
              <KVTable
                title="The terrestrial sphere (SS i.59–61)"
                rows={[
                  ["Diameter", `${yojanas(earth.earth_diameter_yojanas)} yojanas`],
                  [
                    "Circumference",
                    `${yojanas(earth.earth_circumference_yojanas, 3)} yojanas — diameter × √10`,
                  ],
                  [
                    "Corrected circumference",
                    `${yojanas(earth.corrected_circumference_yojanas, 3)} yojanas on this parallel`,
                  ],
                  ["Desantara", `${yojanas(earth.desantara.yojanas, 3)} yojanas · ${earth.desantara.ghatis.toFixed(4)} ghatis`],
                  [
                    "Correction to the Sun",
                    `${earth.desantara.corrections_arcmin.Sun.toFixed(4)}′`,
                  ],
                  [
                    "Correction to the Moon",
                    `${earth.desantara.corrections_arcmin.Moon.toFixed(4)}′`,
                  ],
                ]}
              />
              <p className="ss-note">{earth.desantara.note}</p>
              <KVTable
                title="The sphere at this latitude (SS xii.42–56)"
                rows={[
                  ["Situation", earth.sphere_aspect.kind],
                  ["Elevation of the pole", `${earth.sphere_aspect.pole_altitude.toFixed(2)}°`],
                  ["Co-latitude", `${earth.sphere_aspect.colatitude.toFixed(2)}°`],
                  ["Hemisphere", earth.sphere_aspect.hemisphere],
                  [
                    "Day at no latitude",
                    earth.sphere_aspect.day_ghatis === null
                      ? "varies with declination — see Place & Time"
                      : `${earth.sphere_aspect.day_ghatis} ghatis`,
                  ],
                  ["", earth.sphere_aspect.description],
                ]}
              />
              <div className="ss-block">
                <h3>Parallels of the chapter (SS xii.60–68)</h3>
                <GridTable
                  headers={["Parallel", "Latitude", "From the equator", "Effect", "Verse"]}
                  rows={[
                    [
                      "Sixty-nadi day",
                      `${earth.polar_day_limit.latitude.toFixed(2)}°`,
                      `${yojanas(earth.polar_day_limit.yojanas_from_equator, 1)} yojanas`,
                      `the day reaches sixty nadis once a year (obliquity ${earth.polar_day_limit.obliquity}°)`,
                      earth.polar_day_limit.verse,
                    ],
                    ...earth.invisibility_limits.map((limit) => [
                      `${limit.signs_invisible} signs lost`,
                      `${limit.latitude.toFixed(2)}°`,
                      `${yojanas(limit.yojanas_from_equator, 1)} yojanas`,
                      `the Sun is unseen for ${limit.signs_invisible} signs (declination ${limit.declination?.toFixed(2)}°)`,
                      limit.verse,
                    ]),
                    [
                      "Overhead band",
                      `${earth.solar_overhead_band.degrees.toFixed(2)}°`,
                      `${yojanas(earth.solar_overhead_band.yojanas, 1)} yojanas`,
                      "a fifteenth of the circumference, where the Sun passes overhead",
                      "SS.12.68",
                    ],
                  ]}
                />
              </div>
            </>
          )}
        </>
      )}

      {tab === "Orbits & Distances" && orbits && (
        <>
          <p className="ss-note">{orbits.summary}</p>
          <KVTable
            rows={[
              [
                "Daily motion, every planet alike",
                `${yojanas(orbits.daily_linear_motion_yojanas, 3)} yojanas (SS xii.82)`,
              ],
              ["The Moon's orbit", `${yojanas(orbits.moon_orbit_yojanas)} yojanas (SS xii.85)`],
              [
                "The orbit of the ether",
                `${yojanas(orbits.ether_orbit_yojanas)} yojanas — the limit of the Sun's rays (SS xii.81, 90)`,
              ],
              ["Outward from the earth", orbits.order_outward.join(" · ")],
            ]}
          />
          <GridTable
            headers={[
              "Body",
              "Orbit (yojanas)",
              "As the text states it",
              "Difference",
              "Distance (yojanas)",
              "Daily motion",
              "Revolutions / kalpa",
              "Verse",
            ]}
            rows={orbits.orbits.map((o) => [
              o.body.replace("_", " "),
              yojanas(o.orbit_yojanas, 1),
              o.stated_yojanas === null ? "—" : yojanas(o.stated_yojanas),
              o.stated_difference === null ? "—" : o.stated_difference.toFixed(2),
              yojanas(o.distance_yojanas, 1),
              `${o.daily_motion_arcmin.toFixed(3)}′`,
              yojanas(o.revolutions_per_kalpa),
              o.verse ?? "—",
            ])}
          />
        </>
      )}

      {tab === "Cosmic Time" && (
        <>
          <DateInput value={date} onChange={setDate} withZone />
          <div className="field-row">
            <button onClick={loadTime} disabled={loading}>
              {loading ? "Computing…" : "Compute"}
            </button>
          </div>
          {time && (
            <>
              <p className="ss-note">{time.summary}</p>
              <div className="two-col">
                <KVTable
                  title="Regents of time (SS xii.78–79)"
                  rows={[
                    ["Of the day", time.regents.day],
                    ["Of the 30-day month", time.regents.month],
                    ["Of the 360-day year", time.regents.year],
                    ["Downward order", time.regents.order.join(" → ")],
                  ]}
                />
                <KVTable
                  title="Brahma's present day"
                  rows={[
                    ["Years elapsed", yojanas(time.brahma_day.years_elapsed)],
                    ["Years remaining", yojanas(time.brahma_day.years_remaining)],
                    [
                      "Elapsed",
                      `${(time.brahma_day.fraction_elapsed * 100).toFixed(4)}% of an Aeon of ${yojanas(time.brahma_day.kalpa_years)} years`,
                    ],
                  ]}
                />
              </div>
              <div className="ss-block">
                <h3>Lords of the twenty-four horas, from sunrise</h3>
                <GridTable
                  headers={["Hora", "Lord", "Hora", "Lord", "Hora", "Lord", "Hora", "Lord"]}
                  rows={[0, 1, 2, 3, 4, 5].map((row) =>
                    [0, 1, 2, 3].flatMap((col) => {
                      const index = row + col * 6;
                      return [String(index + 1), time.regents.horas[index]];
                    }),
                  )}
                />
              </div>
              <div className="ss-block">
                <h3>The day and night of the orders of beings (SS xii.74)</h3>
                <GridTable
                  headers={["Beings", "Station", "Day", "Night", "Verse"]}
                  rows={time.day_and_night.map((row) => [
                    row.beings,
                    row.station,
                    row.day,
                    row.night,
                    row.verse,
                  ])}
                />
              </div>
            </>
          )}
        </>
      )}

      {tab === "Worlds" && worlds && (
        <>
          <p className="ss-note">{worlds.summary}</p>
          <div className="ss-block">
            <h3>The reference places (SS xii.34–44)</h3>
            <GridTable
              headers={["Place", "IAST", "Latitude", "Longitude", "Clime", "Local hour at Yamakoti noon", "Verse"]}
              rows={worlds.reference_places.map((p) => [
                p.name,
                p.iast,
                `${p.latitude}°`,
                p.longitude === null ? "— (a pole)" : `${p.longitude}°`,
                p.clime ?? "—",
                p.longitude === null
                  ? "—"
                  : clockTime(worlds.cities_clock_at_yamakoti_noon[p.name]),
                p.verse,
              ])}
            />
          </div>
          <div className="ss-block">
            <h3>The seven patalas (SS xii.33)</h3>
            <p className="ss-note">{worlds.patalas.description}</p>
            <p className="ss-note">{worlds.note}</p>
          </div>
          <div className="ss-block">
            <h3>The creation (SS xii.13–28)</h3>
            <GridTable
              headers={["#", "Agent", "Act", "Verse"]}
              rows={worlds.creation_sequence.map((s) => [
                String(s.order),
                s.agent,
                s.act,
                s.verse,
              ])}
            />
          </div>
          <div className="two-col">
            <div className="ss-block">
              <h3>The elements (SS xii.23)</h3>
              <GridTable
                headers={["#", "Element", "IAST", "Qualities"]}
                rows={worlds.elements.map((e) => [
                  String(e.order),
                  e.name,
                  e.iast,
                  String(e.qualities),
                ])}
              />
            </div>
            <div className="ss-block">
              <h3>Whence the planets arose (SS xii.22–24)</h3>
              <GridTable
                headers={["Planet", "From", "Verse"]}
                rows={worlds.planet_origins.map((o) => [o.planet, o.origin, o.verse])}
              />
            </div>
          </div>
          <div className="ss-block">
            <h3>The order of the spheres, outward (SS xii.29–31)</h3>
            <GridTable
              headers={["#", "Sphere", "IAST", "Kind"]}
              rows={worlds.orbital_order.map((o) => [
                String(o.rank),
                o.name,
                o.iast,
                o.kind,
              ])}
            />
          </div>
          <div className="ss-block">
            <h3>Maya's inquiries (SS xii.1–9)</h3>
            <GridTable
              headers={["#", "Question", "Asked at", "Answered in"]}
              rows={worlds.inquiries.map((q) => [
                String(q.number),
                q.question,
                q.verse,
                q.answered_in,
              ])}
            />
          </div>
        </>
      )}
    </div>
  );
}
