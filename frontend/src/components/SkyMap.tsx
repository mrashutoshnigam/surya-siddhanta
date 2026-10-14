import { useState } from "react";

interface StarPoint {
  name: string;
  right_ascension: number;
  declination: number;
}

const WIDTH = 480;
const HEIGHT = 260;
const PAD = 30;

function project(ra: number, dec: number) {
  const x = PAD + (ra / 360) * (WIDTH - 2 * PAD);
  const y = PAD + ((90 - dec) / 180) * (HEIGHT - 2 * PAD);
  return { x, y };
}

export function SkyMap({ stars, highlight }: { stars: StarPoint[]; highlight?: string }) {
  const [hover, setHover] = useState<string | null>(null);

  return (
    <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} width="100%" style={{ maxWidth: 560 }}>
      <rect x={PAD} y={PAD} width={WIDTH - 2 * PAD} height={HEIGHT - 2 * PAD} fill="none" stroke="var(--hairline)" />
      <line
        x1={PAD}
        y1={PAD + (HEIGHT - 2 * PAD) / 2}
        x2={WIDTH - PAD}
        y2={PAD + (HEIGHT - 2 * PAD) / 2}
        stroke="var(--hairline)"
      />
      <text x={PAD} y={HEIGHT - PAD + 14} fontSize={9} fill="var(--ink-mute)">
        RA 0h
      </text>
      <text x={WIDTH - PAD - 30} y={HEIGHT - PAD + 14} fontSize={9} fill="var(--ink-mute)">
        RA 24h
      </text>

      {stars.map((s) => {
        const { x, y } = project(s.right_ascension, s.declination);
        const active = s.name === highlight || s.name === hover;
        return (
          <g key={s.name} onMouseEnter={() => setHover(s.name)} onMouseLeave={() => setHover(null)}>
            <circle cx={x} cy={y} r={active ? 5 : 3} fill={s.name === highlight ? "var(--primary)" : "var(--ink-mute)"} />
            {active && (
              <text x={x + 6} y={y - 6} fontSize={10} fill="var(--ink)">
                {s.name}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}
