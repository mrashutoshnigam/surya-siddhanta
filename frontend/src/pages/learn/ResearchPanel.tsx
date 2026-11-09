import { useId, useState } from "react";
import data from "./mars-evaluation.json";

export function downloadJson(value: unknown, filename: string) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(value, null, 2)], { type: "application/json" }));
  const anchor = document.createElement("a");
  anchor.href = url; anchor.download = filename;
  document.body.appendChild(anchor); anchor.click(); anchor.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function ResearchPanel() {
  const [start, setStart] = useState(1950);
  const titleId = useId();
  const window = data.windows.find(w => w.start === start)!;
  const bound = Math.max(2, Math.ceil(window.max_abs / 2) * 2);
  const x = (year: number) => 60 + ((year - start + 0.5) / 100) * 660;
  const y = (value: number) => 130 - value / bound * 95;
  const upper = window.bins.map(b => `${x(b.year)},${y(b.max)}`).join(" L ");
  const lower = [...window.bins].reverse().map(b => `${x(b.year)},${y(b.min)}`).join(" L ");
  const average = window.bins.map(b => `${x(b.year)},${y(b.mean)}`).join(" L ");

  return <section className="lab-research" aria-labelledby="lab-research-title">
    <div className="lab-section-heading">
      <div><p className="lab-eyebrow">Compare · saved research</p><h2 id="lab-research-title">How close is the model?</h2></div>
      <label>Evaluation window
        <select value={start} onChange={e => setStart(Number(e.target.value))}>
          {data.windows.map(w => <option key={w.start} value={w.start}>{w.start}–{w.start + 99} CE</option>)}
        </select>
      </label>
    </div>
    <p>Mars in the Surya Siddhanta compared with JPL DE440. This saved study is independent of the lesson date above.</p>
    <div className="lab-research-metrics">
      <div><span>RMS longitude error</span><strong>{window.rms.toFixed(3)}°</strong><small>Root mean square across the window</small></div>
      <div><span>Largest sampled difference</span><strong>{window.max_abs.toFixed(3)}°</strong><small>Absolute longitude error</small></div>
      <div><span>Evaluated positions</span><strong>{window.n.toLocaleString("en-IN")}</strong><small>One sample every ten days</small></div>
    </div>
    <figure className="lab-research-figure">
      <svg viewBox="0 0 760 280" role="img" aria-labelledby={titleId}>
        <title id={titleId}>Mars longitude error, {start} to {start + 99}. RMS {window.rms.toFixed(3)} degrees; maximum absolute error {window.max_abs.toFixed(3)} degrees. Shading shows each year's sampled range; the line shows its mean.</title>
        {[-bound, 0, bound].map(v => <g key={v}>
          <line x1="60" x2="720" y1={y(v)} y2={y(v)} className={v === 0 ? "lab-chart-zero" : "lab-chart-grid"} />
          <text x="48" y={y(v) + 4} textAnchor="end">{v > 0 ? "+" : ""}{v}°</text>
        </g>)}
        <path d={`M ${upper} L ${lower} Z`} className="lab-chart-band" />
        <path d={`M ${average}`} className="lab-chart-line" />
        {[0, 25, 50, 75, 99].map(n => <text key={n} x={x(start + n)} y="252" textAnchor="middle">{start + n}</text>)}
        <text x="60" y="16">SS − DE440 · tropical longitude</text>
      </svg>
      <figcaption>Shading: annual minimum–maximum of sampled errors. Line: annual mean. Positive values put SS ahead of DE440; negative values put it behind. The vertical scale adapts to the selected window.</figcaption>
    </figure>
    <details className="lab-details"><summary>Read the method and limitations</summary>
      <p>{data.frame}</p><p>{data.time}</p>
      <p>RMS is computed from every sample in the selected window, before annual aggregation. Ten-day sampling does not establish the largest error between samples or eclipse timing accuracy. Future dates show model extrapolation.</p>
      <p>These are the repository’s saved evaluation results, not a fresh independent validation. The lesson dial is sidereal; this comparison is tropical.</p>
      <p>Source: <code>{data.source}</code><br />SHA-256: <code className="lab-hash">{data.source_sha256}</code></p>
    </details>
    <button type="button" className="lab-secondary" onClick={() => downloadJson({ ...data, windows: [window] }, `mars-de440-${start}-${start + 99}.json`)}>Download this window’s evidence ↓</button>
  </section>;
}
