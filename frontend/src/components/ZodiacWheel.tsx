import { useState } from "react";

const RASHI_NAMES = [
  "Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
  "Tula", "Vrishchika", "Dhanu", "Makara", "Kumbha", "Meena",
];

interface Planet {
  planet: string;
  true_longitude: number;
}

const SIZE = 360;
const CENTER = SIZE / 2;
const OUTER_R = 160;
const INNER_R = 130;
const LABEL_R = 145;
const PLANET_R = 105;

function polar(deg: number, r: number) {
  // 0deg (Aries start) at the top, increasing clockwise.
  const rad = ((deg - 90) * Math.PI) / 180;
  return { x: CENTER + r * Math.cos(rad), y: CENTER + r * Math.sin(rad) };
}

export function ZodiacWheel({ planets }: { planets: Planet[] }) {
  const [hover, setHover] = useState<string | null>(null);

  return (
    <svg viewBox={`0 0 ${SIZE} ${SIZE}`} width="100%" style={{ maxWidth: 420 }}>
      <circle cx={CENTER} cy={CENTER} r={OUTER_R} fill="none" stroke="var(--primary)" strokeWidth={1.5} />
      <circle cx={CENTER} cy={CENTER} r={INNER_R} fill="none" stroke="var(--hairline)" strokeWidth={1} />

      {RASHI_NAMES.map((name, i) => {
        const startDeg = i * 30;
        const { x: x1, y: y1 } = polar(startDeg, INNER_R);
        const { x: x2, y: y2 } = polar(startDeg, OUTER_R);
        const label = polar(startDeg + 15, LABEL_R);
        return (
          <g key={name}>
            <line x1={x1} y1={y1} x2={x2} y2={y2} stroke="var(--hairline)" strokeWidth={1} />
            <text x={label.x} y={label.y} fontSize={9} textAnchor="middle" fill="var(--ink-mute)">
              {name}
            </text>
          </g>
        );
      })}

      {planets.map((p) => {
        const pos = polar(p.true_longitude, PLANET_R);
        const isHover = hover === p.planet;
        return (
          <g
            key={p.planet}
            onMouseEnter={() => setHover(p.planet)}
            onMouseLeave={() => setHover(null)}
          >
            <circle cx={pos.x} cy={pos.y} r={isHover ? 6 : 4} fill="var(--primary)" stroke="var(--canvas)" strokeWidth={1} />
            <text x={pos.x} y={pos.y - 8} fontSize={isHover ? 11 : 9} textAnchor="middle" fill="var(--ink)">
              {p.planet}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
