import { useState } from "react";
import { KVTable } from "../../../components/Tables";
import { Slider } from "../../../components/VerseCard";
import { fmt } from "../ch01/scale";
import { useLastProbe } from "./probe";
import type { LambanaCard, LambanaProbe } from "./types";

/**
 * v.8-9 — parallax in longitude (lambana).
 *
 * The sine of the interval between the madhyalagna and the Sun, over the
 * divisor: 4 × drggati × sin(interval) nadis. Applied by v.9: subtracted
 * from the end of the lunar day when the Sun is the greater, added when less.
 * The sliders move the interval and drkksepa to show how each moves it.
 */
export function V08Lambana({ card }: { card: LambanaCard }) {
  const [interval, setInterval_] = useState(card.interval);
  const [drkksepa, setDrkksepa] = useState(Math.abs(card.drkksepa));
  const result = useLastProbe<LambanaProbe>(
    { card: "v.8-9", interval, drkksepa },
    { drggati: card.drggati, verse_ghatis: card.verse_ghatis, verse_arcmin: card.verse_arcmin },
  );

  return (
    <>
      <Slider label="Sun − madhyalagna" value={interval} min={-180} max={180} step={1} suffix="°" onChange={setInterval_} />
      <Slider label="Drkksepa" value={drkksepa} min={0} max={80} step={1} suffix="°" onChange={setDrkksepa} />
      <KVTable
        rows={[
          ["Drggati (cos drkksepa)", fmt(result.drggati)],
          [
            "Lambana, applied (nadis)",
            <strong>{fmt(result.verse_ghatis)}</strong>,
          ],
          ["…as motion of Moon over Sun", `${fmt(result.verse_arcmin)}′`],
          [
            "This new moon, by the verse",
            `${fmt(card.verse_arcmin)}′ — ${card.rule === "subtract" ? "subtract from" : "add to"} the end of the lunar day`,
          ],
          ["This new moon, by the library", `${fmt(card.library_arcmin)}′ (${fmt(card.library_ghatis)} nadis)`],
        ]}
      />
      <p className="ss-note">
        Negative means subtract. The library measures the Moon from the nonagesimal; the verse
        measures the Sun from the madhyalagna. At conjunction they are the same to within a
        few minutes of arc.
      </p>
    </>
  );
}
