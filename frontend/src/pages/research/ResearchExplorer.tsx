import { useId, useState } from "react";
import { Link } from "react-router-dom";
import { downloadJson } from "../learn/ResearchPanel";
import data from "./research-data.json";
import "./research.css";

type Variant = "naive" | "deltat";
const labels = { naive: "Naïve time", deltat: "Time-aligned" };
const getSeries = (body: string, variant: Variant) => data.series.find(s => s.body === body && s.variant === variant)!;
const fmt = (n: number) => n.toFixed(3);

export function ResearchExplorer() {
  const [body, setBody] = useState("Mars");
  const [start, setStart] = useState(1950);
  const [variant, setVariant] = useState<Variant>("deltat");
  const id = useId();
  const windows = getSeries(body, variant).windows;
  const selected = windows.find(w => w.start === start)!;
  const naive = getSeries(body, "naive").windows.find(w => w.start === start)!;
  const aligned = getSeries(body, "deltat").windows.find(w => w.start === start)!;
  const bound = Math.max(2, Math.ceil(Math.max(naive.max_abs, aligned.max_abs) / 2) * 2);
  const x = (year: number) => 70 + (year - start + 2.5) / 100 * 780;
  const y = (value: number) => 170 - value / bound * 120;
  const line = (bins: typeof selected.bins, key: "min" | "max" | "mean") => bins.map(b => `${x(b.year)},${y(b[key])}`).join(" L ");
  const band = `M ${line(selected.bins, "max")} L ${line([...selected.bins].reverse(), "min")} Z`;
  const maxRms = Math.max(...data.series.filter(s => s.variant === variant).flatMap(s => s.windows.map(w => w.rms)));
  const evidence = { body, start, end: start + 99, selected_variant: variant, sources: data.sources, frame: data.frame, time: data.time, residual: data.residual, sample_step_days: data.sample_step_days, chart_bin_years: data.chart_bin_years, naive, deltat: aligned };
  function csvDownload() {
    const rows = ["body,variant,start_year,end_year,n,mean_deg,rms_deg,max_abs_deg,source_path,source_sha256,frame,residual,time_convention,sample_step_days"];
    const escape = (value: string | number) => `"${String(value).split('"').join('""')}"`;
    for (const v of ["naive", "deltat"] as const) {
      const w = v === "naive" ? naive : aligned;
      rows.push([body, v, start, start + 99, w.n, w.mean, w.rms, w.max_abs, data.sources[v].path, data.sources[v].sha256, data.frame, data.residual, data.time[v], data.sample_step_days].map(escape).join(","));
    }
    const url = URL.createObjectURL(new Blob([rows.join("\n") + "\n"], { type: "text/csv;charset=utf-8" }));
    const a = document.createElement("a"); a.href = url; a.download = `ss-de440-${body.toLowerCase()}-${start}.csv`;
    document.body.appendChild(a); a.click(); a.remove(); window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  return <div className="research-explorer">
    <header className="research-header"><p className="research-eyebrow">Research explorer / JPL DE440</p><h1>Measure the model.</h1><p>Eight bodies. Eleven centuries. Explore the saved longitude comparison and see what changes when the reference time is aligned.</p><div className="research-scope"><span>1550–2649 CE</span><span>40,176 epochs per body</span><span>10-day sampling</span></div></header>
    <section aria-labelledby="research-matrix-title">
      <div className="research-heading"><div><p className="research-eyebrow">Overview</p><h2 id="research-matrix-title">Where does the error grow?</h2></div><div className="research-treatments" role="group" aria-label="Time treatment">{(["deltat", "naive"] as const).map(v => <button type="button" key={v} aria-pressed={variant === v} onClick={() => setVariant(v)}>{labels[v]}</button>)}</div></div>
      <p>Each cell shows RMS longitude error in degrees. Select a cell to inspect its evidence. Colour intensity uses one shared scale across this matrix.</p>
      <div className="research-matrix-scroll" tabIndex={0} role="region" aria-label="Scrollable RMS error matrix"><table className="research-matrix"><caption>{labels[variant]} · RMS error (degrees) · darker cells indicate larger errors</caption><thead><tr><th scope="col">Body</th>{windows.map(w => <th scope="col" key={w.start}>{w.start}<br /><span>–{w.start + 99}</span></th>)}</tr></thead><tbody>{data.bodies.map(b => <tr key={b}><th scope="row">{b}</th>{getSeries(b, variant).windows.map(w => <td key={w.start}><button type="button" aria-label={`${b}, ${w.start} to ${w.start + 99}, RMS ${fmt(w.rms)} degrees`} aria-pressed={body === b && start === w.start} style={{ backgroundColor: `color-mix(in srgb, var(--primary-text) ${8 + w.rms / maxRms * 40}%, var(--canvas))` }} onClick={() => { setBody(b); setStart(w.start); }}>{w.rms.toFixed(2)}</button></td>)}</tr>)}</tbody></table></div>
      <p className="research-caption">Rahu is the ascending lunar node. The last windows include future extrapolations. These are sampled longitude errors, not eclipse timing errors.</p>
    </section>
    <section className="research-detail" aria-labelledby="research-detail-title">
      <div className="research-heading"><div><p className="research-eyebrow">Inspect</p><h2 id="research-detail-title">{body} · {start}–{start + 99}</h2></div><div className="research-selectors"><label>Body<select aria-label="Body" value={body} onChange={e => setBody(e.target.value)}>{data.bodies.map(b => <option key={b}>{b}</option>)}</select></label><label>Window<select aria-label="Window" value={start} onChange={e => setStart(Number(e.target.value))}>{windows.map(w => <option key={w.start} value={w.start}>{w.start}–{w.start + 99}</option>)}</select></label></div></div>
      <p role="status">Showing {labels[variant].toLowerCase()} shading for {body}; both time treatments share the same vertical scale.</p>
      <div className="research-stats-scroll"><table className="research-stats"><caption>Statistics use all {selected.n.toLocaleString("en-IN")} samples in this window, before chart aggregation.</caption><thead><tr><th scope="col">Treatment</th><th scope="col">RMS error</th><th scope="col">Mean signed error</th><th scope="col">Maximum absolute error</th></tr></thead><tbody>{(["deltat", "naive"] as const).map(v => { const w = v === "naive" ? naive : aligned; return <tr key={v}><th scope="row">{labels[v]}</th><td>{fmt(w.rms)}°</td><td>{w.mean > 0 ? "+" : ""}{fmt(w.mean)}°</td><td>{fmt(w.max_abs)}°</td></tr>; })}</tbody></table></div>
      <figure className="research-plot"><div className="research-plot-scroll" tabIndex={0} role="region" aria-label="Scrollable longitude error chart"><svg viewBox="0 0 900 355" role="img" aria-labelledby={id}><title id={id}>{body} longitude errors, {start} to {start + 99}. Time-aligned RMS {fmt(aligned.rms)} degrees; naïve RMS {fmt(naive.rms)} degrees. Shading shows five-year sampled ranges for {labels[variant]}.</title><text x="70" y="20">SS − DE440 · tropical longitude</text>{[-bound, 0, bound].map(v => <g key={v}><line x1="70" x2="850" y1={y(v)} y2={y(v)} className={v === 0 ? "research-zero" : "research-grid"} /><text x="55" y={y(v) + 5} textAnchor="end">{v > 0 ? "+" : ""}{v}°</text></g>)}<path d={band} className="research-band" /><path d={`M ${line(aligned.bins, "mean")}`} className="research-aligned" /><path d={`M ${line(naive.bins, "mean")}`} className="research-naive" />{[0, 25, 50, 75, 99].map(n => <text key={n} x={70 + n / 100 * 780} y="325" textAnchor="middle">{start + n}</text>)}</svg></div><figcaption><span className="research-legend"><i />Time-aligned mean <i className="is-dashed" />Naïve mean</span>Shading preserves the minimum and maximum sampled error in each five-year group. Lines connect group means; they are not continuous trajectories. The axis adapts between body/window selections.</figcaption></figure>
      <div className="research-interpretation"><h3>What the comparison can tell us</h3><p>Time alignment changes the reference epoch, not the SS formulas. In this window, naïve RMS minus time-aligned RMS is <strong>{(naive.rms - aligned.rms).toFixed(3)}°</strong>. A positive value means the aligned treatment has lower RMS here; a negative value means it has higher RMS. This is a diagnostic, not a fitted correction to the historical model.</p></div>
      <div className="research-actions"><button type="button" onClick={() => downloadJson(evidence, `ss-de440-${body.toLowerCase()}-${start}.json`)}>Download evidence JSON ↓</button><button type="button" onClick={csvDownload}>Download statistics CSV ↓</button><Link to="/learn">Explore the Mars calculation →</Link></div>
    </section>
    <details className="research-method"><summary>Methods, provenance and limits</summary><h3>Reference frame</h3><p>{data.frame}</p><h3>Time conventions</h3><p><strong>Naïve:</strong> {data.time.naive}</p><p><strong>Time-aligned:</strong> {data.time.deltat}</p><p>The time-aligned label includes the meridian conversion and an approximate Delta-T model; it does not imply exact historical or future time conversion.</p><h3>Scope of evidence</h3><p>These are the repository’s saved paper results, not a live JPL request or independent revalidation. Neither historical panchang practice nor student learning outcomes are measured. Ten-day sampling can miss extrema between samples. Five-year chart grouping can hide short-period structure; full-sample statistics and sampled extrema are preserved.</p><p>For Rahu, the reference is derived from the Moon’s orbital angular momentum; it is not a physical planet. Positive residual means the SS tropical longitude is ahead of the reference along the wrapped angular difference.</p>{Object.entries(data.sources).map(([name, source]) => <p key={name}><strong>{labels[name as Variant]}</strong><br /><code>{source.path}</code><br /><code>{source.sha256}</code></p>)}<p>See the repository’s evaluation paper and REPRODUCE.md for the underlying study and source CSVs.</p></details>
  </div>;
}
