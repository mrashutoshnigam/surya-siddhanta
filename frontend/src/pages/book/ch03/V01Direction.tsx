import { useState } from "react";
import { KVTable } from "../../../components/Tables";
import { Slider } from "../../../components/VerseCard";
import { fmt } from "../ch01/scale";
import { useLastProbe } from "./probe";
import type { DirectionCard, DirectionResult } from "./types";

/**
 * iii.1-4 — the north-south line from two shadow tips.
 *
 * The two tips are marked where the shadow's end touches the circle before
 * and after noon; the line through them runs east-west and its bisector is
 * the meridian. The angle is the library's, not re-derived here.
 */
export function V01Direction({ card }: { card: DirectionCard }) {
  const [tip1, setTip1] = useState<[number, number]>(card.tip1);
  const [tip2, setTip2] = useState<[number, number]>(card.tip2);
  const [noonShadowDirection, setNoonShadowDirection] = useState(card.noon_shadow_direction);
  const result = useLastProbe<DirectionResult>(
    { card: "iii.1-4", x1: tip1[0], y1: tip1[1], x2: tip2[0], y2: tip2[1], noon_shadow_direction: noonShadowDirection },
    card,
  );

  return (
    <>
      <Slider label="Forenoon tip, east–west" value={tip1[0]} min={-20} max={20} step={0.5} suffix="digits" onChange={(v) => setTip1([v, tip1[1]])} />
      <Slider label="Forenoon tip, north–south" value={tip1[1]} min={-20} max={20} step={0.5} suffix="digits" onChange={(v) => setTip1([tip1[0], v])} />
      <Slider label="Afternoon tip, east–west" value={tip2[0]} min={-20} max={20} step={0.5} suffix="digits" onChange={(v) => setTip2([v, tip2[1]])} />
      <Slider label="Afternoon tip, north–south" value={tip2[1]} min={-20} max={20} step={0.5} suffix="digits" onChange={(v) => setTip2([tip2[0], v])} />
      <label>
        Noon shadow points
        <select value={noonShadowDirection} onChange={(e) => setNoonShadowDirection(e.target.value as "north" | "south")}>
          <option value="north">North</option>
          <option value="south">South</option>
        </select>
      </label>
      <KVTable
        rows={[
          ["Midpoint of the tips", `${fmt(result.midpoint[0])}, ${fmt(result.midpoint[1])}`],
          ["Bisector, from north", `${fmt(result.ns_angle)}°`],
          ["Direction", <strong>{result.cardinal}</strong>],
        ]}
      />
    </>
  );
}
