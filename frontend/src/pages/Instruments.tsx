import { useEffect, useState } from "react";
import { api } from "../api";
import { DateInput, LatLonInput, DEFAULT_LATLON, todayValue } from "../components/Inputs";
import type { DateValue, LatLon } from "../components/Inputs";
import { ErrorBox, GridTable, KVTable, PageHeader } from "../components/Tables";
import {
  ArmillarySphere3D,
  HOOP_GROUPS,
  webglAvailable,
} from "../components/ArmillarySphere3D";
import type { HoopGroup, SphereData, SphereHoopData, SpherePointData } from "../components/ArmillarySphere3D";

// Chapter 13 has three parts — the armillary sphere, the clepsydra, and the
// instruments that find time — plus a descriptive catalog; one tab each,
// matching the four /calc/instruments routes. This page is lazy-loaded from
// App.tsx so the three.js bundle is only fetched when it is opened.
const TABS = ["Armillary Sphere", "Clepsydra", "Shadow & Staff", "Catalog"] as const;
type Tab = (typeof TABS)[number];

type Instrument = "nara" | "cakra" | "dhanus" | "yashti";

interface SphereResult extends SphereData {
  pole_altitude: number;
  ayanamsha: number;
  sines: Record<string, number>;
  chord_of_thirty: number;
  summary: string;
}

interface ClepsydraReading {
  sinkings: number;
  partial: number;
  ghatis: number;
  ghati_pala_vipala: string;
  clock: string;
  total_minutes: number;
}

interface ClepsydraResult {
  sinkings_per_day: number;
  elapsed?: ClepsydraReading;
  for_ghatis?: ClepsydraReading;
  day_and_night?: {
    day_ghatis: number;
    night_ghatis: number;
    sun_declination: number;
    day_sinkings: ClepsydraReading;
    night_sinkings: ClepsydraReading;
  };
  drift?: {
    minutes_per_sinking: number;
    error_minutes_per_sinking: number;
    reading_error_minutes_per_day: number;
  };
  vessel: Record<string, string | number>;
  summary: string;
}

interface TimeResult {
  instrument_name: string;
  reading: number;
  reading_unit: string;
  ghatis_since_sunrise: number;
  ghatis_to_sunset: number;
  hours_since_sunrise: number;
  sun_altitude_deg: number;
  hour_angle_deg: number;
  sun_declination_deg: number;
  half_day_ghatis: number;
  source: "verse" | "commentary";
  verse: string;
  extra: Record<string, number>;
  summary: string;
}

interface CatalogResult {
  chapter_name_en: string;
  note: string;
  missing_verses_note: string;
  instruments: {
    key: string;
    name: string;
    iast: string;
    verse: string;
    source: string;
    computable: boolean;
    description: string;
  }[];
  sphere_components: { key: string; name: string; iast: string; verse: string; description: string }[];
  sphere_points: { key: string; name: string; iast: string; verse: string; definition: string; correction?: string }[];
  fixed_stars: {
    name: string;
    identification: string;
    polar_longitude: number;
    polar_latitude: number;
    text: string;
    verse: string;
    corpus_record: string;
    note?: string;
  }[];
  seven_sages: { name: string; identification: string; description: string; note: string; verse: string };
  clepsydra_vessel: Record<string, string | number>;
}

const READING_LABEL: Record<Instrument, string> = {
  nara: "Shadow length",
  cakra: "Altitude on the wheel (°)",
  dhanus: "Altitude on the arc (°)",
  yashti: "Chord, staff tip to horizon point",
};

const DEFAULT_READING: Record<Instrument, number> = { nara: 12, cakra: 45, dhanus: 45, yashti: 1500 };

const deg = (v: number | null | undefined, digits = 2) => (v === null || v === undefined ? "—" : `${v.toFixed(digits)}°`);

function SourceBadge({ source }: { source: "verse" | "commentary" | string }) {
  return (
    <span className={"source-badge " + (source === "verse" ? "verse" : "commentary")}>
      {source === "verse" ? "text" : "commentary"}
    </span>
  );
}

/** A copper bowl floating in its basin, filled to the fraction given. */
function Bowl({ fill }: { fill: number }) {
  const r = 60;
  const cx = 110;
  const top = 50;
  const f = Math.max(0, Math.min(1, fill));
  // The bowl is a hemisphere centred on its rim. The water surface is drawn
  // at a height proportional to the fill, with the half-width of the bowl at
  // that depth.
  const y = top + r - r * f;
  const chord = Math.sqrt(Math.max(0, r * r - (y - top) ** 2));
  return (
    <svg viewBox="0 0 220 150" width="100%" style={{ maxWidth: 260 }} role="img" aria-label="Clepsydra bowl">
      <rect x={10} y={40} width={200} height={100} rx={6} fill="#d6eaf8" stroke="#85c1e9" />
      <path d={`M ${cx - r} ${top} A ${r} ${r} 0 0 0 ${cx + r} ${top} Z`} fill="#f5e6d3" stroke="#a0522d" strokeWidth={3} />
      {f > 0 && (
        <path
          d={`M ${cx - chord} ${y} A ${r} ${r} 0 0 0 ${cx + chord} ${y} Z`}
          fill="#5dade2"
          opacity={0.85}
        />
      )}
      <circle cx={cx} cy={top + r} r={2.5} fill="#333" />
      <text x={cx} y={24} textAnchor="middle" fontSize={11} fill="#555">
        {`bowl ${(f * 100).toFixed(0)}% filled`}
      </text>
    </svg>
  );
}

export function Instruments() {
  const [tab, setTab] = useState<Tab>("Armillary Sphere");
  const [place, setPlace] = useState<LatLon>(DEFAULT_LATLON);
  const [date, setDate] = useState<DateValue>(todayValue());
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);

  // Sphere tab
  const [hour, setHour] = useState(6.5);
  const [includeStars, setIncludeStars] = useState(true);
  const [sphere, setSphere] = useState<SphereResult | null>(null);
  const [visible, setVisible] = useState<Set<HoopGroup>>(
    new Set<HoopGroup>(["great_circles", "solar", "junction_stars", "fixed_stars", "horizon"]),
  );
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(6);
  const [turn, setTurn] = useState(0);
  const [hasWebgl] = useState(webglAvailable);

  // Clepsydra tab
  const [sinkings, setSinkings] = useState(10);
  const [partial, setPartial] = useState(0.5);
  const [ghatis, setGhatis] = useState(17.25);
  const [observed, setObserved] = useState(61);
  const [clepsydra, setClepsydra] = useState<ClepsydraResult | null>(null);

  // Shadow & Staff tab
  const [instrument, setInstrument] = useState<Instrument>("nara");
  const [reading, setReading] = useState(DEFAULT_READING.nara);
  const [gnomon, setGnomon] = useState(12);
  const [staff, setStaff] = useState(3438);
  const [forenoon, setForenoon] = useState(true);
  const [timeResult, setTimeResult] = useState<TimeResult | null>(null);

  // Catalog tab
  const [catalog, setCatalog] = useState<CatalogResult | null>(null);

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

  const loadSphere = () => {
    setPlaying(false);
    setTurn(0);
    run<SphereResult>(
      api.instrumentsSphere({ ...date, ...place, hour, include_stars: includeStars }),
      setSphere,
    );
  };

  const loadClepsydra = () =>
    run<ClepsydraResult>(
      api.instrumentsClepsydra({
        sinkings,
        partial,
        ghatis,
        observed_per_day: observed,
        ...date,
        latitude: place.latitude,
      }),
      setClepsydra,
    );

  const loadTime = () =>
    run<TimeResult>(
      api.instrumentsTime({
        ...date,
        instrument,
        value: reading,
        latitude: place.latitude,
        gnomon,
        staff_length: staff,
        forenoon,
      }),
      setTimeResult,
    );

  useEffect(() => {
    if (tab === "Catalog" && !catalog) {
      run<CatalogResult>(api.instrumentsCatalog({}), setCatalog);
    }
  }, [tab, catalog]);

  function toggleGroup(group: HoopGroup) {
    setVisible((prev) => {
      const next = new Set(prev);
      if (next.has(group)) next.delete(group);
      else next.add(group);
      return next;
    });
  }

  const pointRows = (points: SpherePointData[]) =>
    points.map((p) => [
      p.name,
      deg(p.tropical_longitude),
      deg(p.sidereal_longitude),
      deg(p.right_ascension),
      deg(p.declination),
      p.verse,
    ]);

  const hoopRows = (hoops: SphereHoopData[]) =>
    hoops.map((h) => [
      h.name,
      HOOP_GROUPS.find((g) => g.key === h.group)?.label ?? h.group,
      deg(h.declination),
      h.day_radius === null ? "—" : h.day_radius.toFixed(1),
      h.radius.toFixed(4),
      h.verse,
    ]);

  return (
    <div>
      <PageHeader
        title="Instruments"
        subtitle="The armillary sphere, the sinking-bowl water clock, and finding time with gnomon, wheel, arc and staff — Jyotishopanishad (Ch.13)"
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

      {tab === "Armillary Sphere" && (
        <>
          <DateInput value={date} onChange={setDate} withZone />
          <LatLonInput value={place} onChange={setPlace} />
          <div className="field-row">
            <label>
              Hour (clock time in the zone above)
              <input
                type="number"
                value={hour}
                min={0}
                max={24}
                step={0.25}
                onChange={(e) => setHour(Number(e.target.value))}
              />
            </label>
            <label className="checkbox-label">
              <input type="checkbox" checked={includeStars} onChange={(e) => setIncludeStars(e.target.checked)} />
              Star hoops
            </label>
            <button onClick={loadSphere} disabled={loading}>
              {loading ? "Building…" : "Build sphere"}
            </button>
          </div>

          {sphere && (
            <>
              <p className="ss-note">{sphere.summary}</p>

              <div className="chip-row">
                {HOOP_GROUPS.map((g) => (
                  <label key={g.key} className="chip" style={{ borderColor: g.color }}>
                    <input type="checkbox" checked={visible.has(g.key)} onChange={() => toggleGroup(g.key)} />
                    <span style={{ color: g.color }}>{g.label}</span>
                  </label>
                ))}
              </div>

              <div className="field-row">
                <button onClick={() => setPlaying((p) => !p)}>{playing ? "Pause" : "Set in motion"}</button>
                <label>
                  Speed
                  <select value={speed} onChange={(e) => setSpeed(Number(e.target.value))}>
                    <option value={1}>10 palas / s</option>
                    <option value={6}>1 ghati / s</option>
                    <option value={30}>5 ghatis / s</option>
                  </select>
                </label>
                <label className="range-label">
                  Turned {(turn / 6).toFixed(1)} ghatis
                  <input
                    type="range"
                    min={0}
                    max={360}
                    step={0.5}
                    value={turn}
                    disabled={playing}
                    onChange={(e) => setTurn(Number(e.target.value))}
                  />
                </label>
                <button onClick={() => setTurn(0)} disabled={playing || turn === 0}>
                  Reset
                </button>
              </div>

              {hasWebgl ? (
                <ArmillarySphere3D
                  sphere={sphere}
                  visible={visible}
                  playing={playing}
                  speed={speed}
                  turn={turn}
                  onTurn={setTurn}
                  showPoints={!playing && turn === 0}
                />
              ) : (
                <ErrorBox error="WebGL is not available in this browser, so the sphere cannot be drawn. The tables below carry the same model." />
              )}
              <p className="ss-note">
                Drag to look around. The lagnas and the Sun are shown for the moment set, and hidden once the sphere
                is turned. The lower half is cased in cloth, as v.16 directs. The Meru staff points to the elevated
                pole, {sphere.pole_altitude.toFixed(2)}° above the northern horizon.
              </p>

              <div className="two-col">
                <div>
                  <h3 className="ss-subhead">Points on the sphere (v.10-14)</h3>
                  <GridTable
                    headers={["Point", "Tropical", "Sidereal", "RA", "Decl.", "Verse"]}
                    rows={pointRows([...sphere.points, ...sphere.cardinal_points])}
                  />
                </div>
                <KVTable
                  title="Sines of v.14-15 (R = 3438)"
                  rows={[
                    ["Local sidereal time", deg(sphere.lst_deg)],
                    ["Ayanamsha", deg(sphere.ayanamsha, 3)],
                    ["Sine of declination (krantijya)", sphere.sines.krantijya.toFixed(1)],
                    ["Day-radius (dyujya)", sphere.sines.dyujya.toFixed(1)],
                    ["Earth-sine (kujya)", sphere.sines.kujya.toFixed(1)],
                    ["Ascensional-difference sine (carajya)", sphere.sines.carajya.toFixed(1)],
                    ["Day-measure (antya), great circle", sphere.sines.antya_great_circle.toFixed(1)],
                    [
                      "Day-measure as the verse defines it",
                      `${sphere.sines.antya_small_circle.toFixed(1)} — in the Sun's small circle; Burgess calls this a blunder`,
                    ],
                    ["Chord of 30° (v.11)", sphere.chord_of_thirty.toFixed(1)],
                  ]}
                />
              </div>

              <h3 className="ss-subhead">Hoops ({sphere.hoops.length})</h3>
              <GridTable
                headers={["Hoop", "Group", "Decl.", "Day-radius", "Radius", "Verse"]}
                rows={hoopRows(sphere.hoops)}
              />
            </>
          )}
        </>
      )}

      {tab === "Clepsydra" && (
        <>
          <p className="ss-note">
            "A copper vessel, with a hole in the bottom, set in a basin of pure water, sinks sixty times in a day and
            night" (SS xiii.23) — each sinking is one ghati of 24 minutes.
          </p>
          <div className="field-row">
            <label>
              Sinkings
              <input type="number" min={0} step={1} value={sinkings} onChange={(e) => setSinkings(Number(e.target.value))} />
            </label>
            <label className="range-label">
              Current fill {(partial * 100).toFixed(0)}%
              <input type="range" min={0} max={0.99} step={0.01} value={partial} onChange={(e) => setPartial(Number(e.target.value))} />
            </label>
            <label>
              Ghatis to convert
              <input type="number" min={0} step={0.25} value={ghatis} onChange={(e) => setGhatis(Number(e.target.value))} />
            </label>
            <label>
              Observed sinkings / day
              <input type="number" min={1} step={0.5} value={observed} onChange={(e) => setObserved(Number(e.target.value))} />
            </label>
          </div>
          <DateInput value={date} onChange={setDate} />
          <LatLonInput value={place} onChange={setPlace} />
          <div className="field-row">
            <button onClick={loadClepsydra} disabled={loading}>
              {loading ? "Computing…" : "Compute"}
            </button>
          </div>

          <div className="two-col">
            <Bowl fill={partial} />
            {clepsydra && <p className="ss-note">{clepsydra.summary}</p>}
          </div>

          {clepsydra && (
            <div className="two-col">
              <div>
                {clepsydra.elapsed && (
                  <KVTable
                    title="Sinkings to time"
                    rows={[
                      ["Sinkings", `${clepsydra.elapsed.sinkings} + ${(clepsydra.elapsed.partial * 100).toFixed(0)}% fill`],
                      ["Ghatis-palas-vipalas", clepsydra.elapsed.ghati_pala_vipala],
                      ["Clock time", clepsydra.elapsed.clock],
                    ]}
                  />
                )}
                {clepsydra.for_ghatis && (
                  <KVTable
                    title="Time to sinkings"
                    rows={[
                      ["Ghatis", clepsydra.for_ghatis.ghatis.toFixed(4)],
                      ["Sinkings", `${clepsydra.for_ghatis.sinkings} + ${(clepsydra.for_ghatis.partial * 100).toFixed(0)}% fill`],
                      ["Clock time", clepsydra.for_ghatis.clock],
                    ]}
                  />
                )}
                {clepsydra.drift && (
                  <KVTable
                    title="Drift of the bowl"
                    rows={[
                      ["Minutes per sinking", clepsydra.drift.minutes_per_sinking.toFixed(3)],
                      ["Error per sinking", `${clepsydra.drift.error_minutes_per_sinking.toFixed(3)} min`],
                      ["Reading error per day", `${clepsydra.drift.reading_error_minutes_per_day.toFixed(1)} min`],
                    ]}
                  />
                )}
              </div>
              <div>
                {clepsydra.day_and_night && (
                  <KVTable
                    title="Day and night in sinkings"
                    rows={[
                      ["Sun's declination", deg(clepsydra.day_and_night.sun_declination)],
                      ["Sunrise to sunset", `${clepsydra.day_and_night.day_ghatis.toFixed(3)} sinkings (${clepsydra.day_and_night.day_sinkings.clock})`],
                      ["Sunset to sunrise", `${clepsydra.day_and_night.night_ghatis.toFixed(3)} sinkings (${clepsydra.day_and_night.night_sinkings.clock})`],
                    ]}
                  />
                )}
                <KVTable
                  title="The vessel, per the commentary"
                  rows={Object.entries(clepsydra.vessel)
                    .filter(([k]) => !["description", "note", "verse", "source"].includes(k))
                    .map(([k, v]) => [k.replace(/_/g, " "), String(v)])}
                />
                <p className="ss-note">{String(clepsydra.vessel.note)}</p>
              </div>
            </div>
          )}
        </>
      )}

      {tab === "Shadow & Staff" && (
        <>
          <div className="field-row">
            <label>
              Instrument
              <select
                value={instrument}
                onChange={(e) => {
                  const next = e.target.value as Instrument;
                  setInstrument(next);
                  setReading(DEFAULT_READING[next]);
                  setTimeResult(null);
                }}
              >
                <option value="nara">Man-instrument / gnomon (nara) — text</option>
                <option value="cakra">Wheel (cakra) — commentary</option>
                <option value="dhanus">Arc (dhanus) — commentary</option>
                <option value="yashti">Staff (yashti) — commentary</option>
              </select>
            </label>
            <label>
              {READING_LABEL[instrument]}
              <input type="number" min={0} step={0.1} value={reading} onChange={(e) => setReading(Number(e.target.value))} />
            </label>
            {instrument === "nara" && (
              <label>
                Gnomon (digits)
                <input type="number" min={1} step={1} value={gnomon} onChange={(e) => setGnomon(Number(e.target.value))} />
              </label>
            )}
            {instrument === "yashti" && (
              <label>
                Staff length
                <input type="number" min={1} step={1} value={staff} onChange={(e) => setStaff(Number(e.target.value))} />
              </label>
            )}
            <label>
              Taken
              <select value={forenoon ? "am" : "pm"} onChange={(e) => setForenoon(e.target.value === "am")}>
                <option value="am">before noon</option>
                <option value="pm">after noon</option>
              </select>
            </label>
          </div>
          <DateInput value={date} onChange={setDate} />
          <LatLonInput value={place} onChange={setPlace} />
          <div className="field-row">
            <button onClick={loadTime} disabled={loading}>
              {loading ? "Computing…" : "Find the time"}
            </button>
          </div>

          {timeResult && (
            <>
              <p className="ss-note">{timeResult.summary}</p>
              <KVTable
                title={timeResult.instrument_name}
                rows={[
                  ["Method", <><SourceBadge source={timeResult.source} /> {timeResult.verse}</>],
                  ["Reading", `${timeResult.reading} (${timeResult.reading_unit})`],
                  ["Sun's altitude", deg(timeResult.sun_altitude_deg)],
                  ["Hour angle", deg(timeResult.hour_angle_deg)],
                  ["Sun's declination", deg(timeResult.sun_declination_deg)],
                  ["Ghatis since sunrise", `${timeResult.ghatis_since_sunrise.toFixed(3)} (${timeResult.hours_since_sunrise.toFixed(2)} h)`],
                  ["Ghatis until sunset", timeResult.ghatis_to_sunset.toFixed(3)],
                  ["Half-day", `${timeResult.half_day_ghatis.toFixed(3)} ghatis`],
                  ...Object.entries(timeResult.extra).map(
                    ([k, v]) => [k.replace(/_/g, " "), v.toFixed(3)] as [string, string],
                  ),
                ]}
              />
            </>
          )}
        </>
      )}

      {tab === "Catalog" && catalog && (
        <>
          <p className="ss-note">{catalog.note}</p>
          <p className="ss-note">{catalog.missing_verses_note}</p>

          <h3 className="ss-subhead">Instruments</h3>
          <GridTable
            headers={["Instrument", "Sanskrit", "Verse", "Method", "Computed here", "Description"]}
            rows={catalog.instruments.map((i) => [
              i.name,
              i.iast,
              i.verse,
              <SourceBadge source={i.source} />,
              i.computable ? "yes" : "no",
              i.description,
            ])}
          />

          <h3 className="ss-subhead">Parts of the sphere</h3>
          <GridTable
            headers={["Part", "Sanskrit", "Verse", "Description"]}
            rows={catalog.sphere_components.map((c) => [c.name, c.iast, c.verse, c.description])}
          />

          <h3 className="ss-subhead">Points and sines on the sphere</h3>
          <GridTable
            headers={["Point", "Sanskrit", "Verse", "Definition", "Burgess's correction"]}
            rows={catalog.sphere_points.map((p) => [p.name, p.iast, p.verse, p.definition, p.correction ?? "—"])}
          />

          <h3 className="ss-subhead">Fixed stars on the sphere (viii.10-12, 20-21)</h3>
          <GridTable
            headers={["Star", "Identified as", "Polar long.", "Polar lat.", "Text", "Verse", "Corpus record"]}
            rows={catalog.fixed_stars.map((s) => [
              s.name,
              s.identification,
              deg(s.polar_longitude, 0),
              `${Math.abs(s.polar_latitude)}° ${s.polar_latitude < 0 ? "S" : "N"}`,
              s.note ? `${s.text} — ${s.note}` : s.text,
              s.verse,
              s.corpus_record,
            ])}
          />
          <p className="ss-note">
            <strong>{catalog.seven_sages.name}</strong> ({catalog.seven_sages.identification}, {catalog.seven_sages.verse}):{" "}
            {catalog.seven_sages.description} {catalog.seven_sages.note}
          </p>

          <KVTable
            title="Clepsydra vessel (commentary to v.23)"
            rows={Object.entries(catalog.clepsydra_vessel)
              .filter(([k]) => !["note", "verse", "source"].includes(k))
              .map(([k, v]) => [k.replace(/_/g, " "), String(v)])}
          />
        </>
      )}
    </div>
  );
}
