import { useId } from "react";

function point(degrees: number, radius: number) {
  const angle = degrees * Math.PI / 180;
  return { x: 250 + radius * Math.cos(angle), y: 250 - radius * Math.sin(angle) };
}

/** Angular directions only: radius is a drawing choice, never an orbital distance. */
export function LongitudeDial({ mean, selected, label }: { mean: number; selected: number; label: string }) {
  const id = useId();
  const m = point(mean, 175);
  const s = point(selected, 175);
  return <svg className="lab-dial" viewBox="0 0 500 500" role="img" aria-labelledby={id}>
    <title id={id}>{label}: {selected.toFixed(4)} degrees. Mean longitude: {mean.toFixed(4)} degrees. Sidereal angles increase counterclockwise from Aries.</title>
    <circle cx="250" cy="250" r="203" className="lab-dial-border" />
    <circle cx="250" cy="250" r="175" className="lab-dial-border" />
    <circle cx="250" cy="250" r="100" className="lab-dial-guide" />
    {Array.from({ length: 72 }, (_, i) => {
      const a = point(i * 5, i % 6 === 0 ? 184 : 194);
      const b = point(i * 5, 203);
      const t = point(i * 5, 222);
      return <g key={i}>
        <line x1={a.x} y1={a.y} x2={b.x} y2={b.y} className="lab-dial-tick" />
        {i % 6 === 0 && <text x={t.x} y={t.y} textAnchor="middle" dominantBaseline="middle">{i * 5}°</text>}
      </g>;
    })}
    <line x1="250" y1="250" x2="425" y2="250" className="lab-dial-guide" />
    <line x1="250" y1="250" x2={m.x} y2={m.y} className="lab-mean-ray" />
    <circle cx={m.x} cy={m.y} r="7" className="lab-mean-point" />
    <line x1="250" y1="250" x2={s.x} y2={s.y} className="lab-selected-ray" />
    <circle cx={s.x} cy={s.y} r="11" className="lab-selected-point" />
    <circle cx="250" cy="250" r="5" className="lab-earth-point" />
    <text x="250" y="278" textAnchor="middle">Earth</text>
  </svg>;
}
