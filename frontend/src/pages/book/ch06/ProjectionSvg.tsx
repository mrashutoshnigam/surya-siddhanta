import type { Pt } from "./types";

const SIZE = 320;
const MID = SIZE / 2;
const MARGIN = 150;

/** One eclipser position to draw, with its label. */
export interface Mark {
  point: Pt | null;
  label: string;
}

/**
 * The figure of SS Ch.6, drawn from the payload's own numbers.
 *
 * The eclipsed body sits at the centre inside the aggregate circle (radius
 * half the sum of the two bodies). Points arrive in the ecliptic frame and
 * are rotated here by the valana, which is how v.2 lays the ecliptic across
 * the deflection circle. The path runs through the contact, middle and
 * separation positions of the eclipser; extra marks (a stick's end, the
 * immersion point) show the eclipser's disk where each falls.
 */
export function ProjectionSvg({
  eclipsedR,
  eclipserR,
  valana,
  contact,
  middle,
  separation,
  marks = [],
}: {
  eclipsedR: number;
  eclipserR: number;
  valana: number;
  contact: Pt | null;
  middle: Pt;
  separation: Pt | null;
  marks?: Mark[];
}) {
  const halfSum = eclipsedR + eclipserR;
  // Fit the eclipser's disk at its far positions too, not just the aggregate circle.
  const scale = MARGIN / (halfSum + eclipserR);
  const v = (valana * Math.PI) / 180;
  const cos = Math.cos(v);
  const sin = Math.sin(v);
  /** Ecliptic frame to screen: rotate by the valana, north up. */
  const place = ([x, y]: Pt): Pt => [
    MID + scale * (x * cos - y * sin),
    MID - scale * (x * sin + y * cos),
  ];
  const [mx, my] = place(middle);
  const ends = contact && separation ? [place(contact), place(separation)] : null;
  const [ex1, ey1] = place([-halfSum, 0]);
  const [ex2, ey2] = place([halfSum, 0]);

  return (
    <svg
      className="projection-svg"
      viewBox={`0 0 ${SIZE} ${SIZE}`}
      role="img"
      aria-label="Projection of the eclipse"
      style={{ maxWidth: 360, width: "100%" }}
    >
      <circle cx={MID} cy={MID} r={halfSum * scale} fill="none" stroke="var(--hairline)" strokeDasharray="4 4" />
      <line x1={ex1} y1={ey1} x2={ex2} y2={ey2} stroke="var(--muted-soft)" strokeDasharray="2 4" />
      <circle cx={MID} cy={MID} r={eclipsedR * scale} fill="var(--surface-strong)" stroke="var(--ink)" />
      <circle cx={MID} cy={MID} r={1.5} fill="var(--ink)" />
      {ends && (
        <line x1={ends[0][0]} y1={ends[0][1]} x2={ends[1][0]} y2={ends[1][1]} stroke="var(--primary)" strokeWidth={1.5} />
      )}
      {ends &&
        ends.map(([x, y], i) => (
          <circle key={i} cx={x} cy={y} r={eclipserR * scale} fill="none" stroke="var(--primary)" strokeOpacity={0.45} />
        ))}
      {ends && <circle cx={mx} cy={my} r={eclipserR * scale} fill="var(--primary)" fillOpacity={0.12} stroke="var(--primary)" />}
      {marks.map((m, i) => {
        if (!m.point) return null;
        const [x, y] = place(m.point);
        return (
          <g key={i}>
            <circle cx={x} cy={y} r={eclipserR * scale} fill="var(--accent-yellow)" fillOpacity={0.18} stroke="var(--accent-yellow)" />
            <circle cx={x} cy={y} r={2.5} fill="var(--accent-yellow)" />
            <text x={x} y={y - 6} textAnchor="middle" fontSize={10} fill="var(--body)">
              {m.label}
            </text>
          </g>
        );
      })}
      <text x={SIZE - 8} y={MID + 4} textAnchor="end" fontSize={11} fill="var(--muted)">E</text>
      <text x={8} y={MID + 4} fontSize={11} fill="var(--muted)">W</text>
      <text x={MID} y={12} textAnchor="middle" fontSize={11} fill="var(--muted)">N</text>
      <text x={MID} y={SIZE - 4} textAnchor="middle" fontSize={11} fill="var(--muted)">S</text>
    </svg>
  );
}
