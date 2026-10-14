/**
 * One Moon drawn as the verses direct (x.10-14): the disc, the lit part, and
 * the cusps turned to the observer's view.
 *
 * Drawn in a frame where the Sun lies to the right, then turned so the Sun
 * lies at `sunAngle` (degrees clockwise from the top of the figure; the
 * library's horn axis less a right angle). The lit part is the limb facing
 * the Sun closed by a terminator ellipse whose half-width is
 * `R * cos(phase)`: it coincides with the limb at new moon, is a straight
 * line at the quarters and bulges past the centre towards the dark side as
 * the Moon fills.
 */
export function MoonDisc({
  elongation,
  sunAngle,
  size = 140,
}: {
  elongation: number;
  sunAngle: number;
  size?: number;
}) {
  const R = 50;
  // Elongation past half a revolution is the same shape on the waning side.
  const phase = elongation <= 180 ? elongation : 360 - elongation;
  const rx = R * Math.cos((phase * Math.PI) / 180);
  const sweep = rx >= 0 ? 0 : 1;
  const lit = `M 0 ${-R} A ${R} ${R} 0 0 1 0 ${R} A ${Math.abs(rx)} ${R} 0 0 ${sweep} 0 ${-R} Z`;
  return (
    <svg
      viewBox="-60 -60 120 120"
      width={size}
      height={size}
      role="img"
      aria-label={`Moon, elongation ${elongation.toFixed(1)} degrees`}
    >
      <circle r={R} fill="#2b2f3a" stroke="#888" strokeWidth={0.8} />
      <g transform={`rotate(${sunAngle - 90})`}>
        <path d={lit} fill="#f3e9b8" />
        <line x1={-R - 6} y1={0} x2={R + 6} y2={0} stroke="#888" strokeWidth={0.5} strokeDasharray="2 2" />
      </g>
      <circle r={R} fill="none" stroke="#888" strokeWidth={0.8} />
    </svg>
  );
}
