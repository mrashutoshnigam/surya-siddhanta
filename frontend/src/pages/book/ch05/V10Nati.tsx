import { useState } from "react";
import { KVTable } from "../../../components/Tables";
import { Slider } from "../../../components/VerseCard";
import { fmt } from "../ch01/scale";
import { useLastProbe } from "./probe";
import type { NatiCard, NatiProbe } from "./types";

/**
 * v.10-12 — parallax in latitude (nati).
 *
 * The drkksepa sine times 49′ (v.11 gives it as the sine ÷ 70 as well). It
 * is south or north as the meridian-sine is (v.12), and is added to the
 * Moon's latitude when they lie the same way, subtracted otherwise.
 */
export function V10Nati({ card }: { card: NatiCard }) {
  const [drkksepa, setDrkksepa] = useState(Math.abs(card.drkksepa));
  const result = useLastProbe<NatiProbe>(
    { card: "v.10-12", drkksepa },
    {
      verse_arcmin: card.verse_arcmin,
      shortcut_arcmin: card.shortcut_arcmin,
      library_arcmin: card.library_arcmin,
    },
  );

  return (
    <>
      <Slider label="Drkksepa" value={drkksepa} min={0} max={80} step={1} suffix="°" onChange={setDrkksepa} />
      <KVTable
        rows={[
          ["49′ × sin drkksepa", <strong>{fmt(result.verse_arcmin)}′</strong>],
          ["sin drkksepa ÷ 70 (radius 3438′)", `${fmt(result.shortcut_arcmin)}′`],
          ["Library (48.76′ × sin, signed)", `${fmt(result.library_arcmin)}′`],
          ["Direction (meridian-sine)", card.meridian_direction],
          ["Moon's latitude at this new moon", `${fmt(card.moon_latitude)}′`],
          [
            card.same_direction ? "Sum with the nati" : "Difference with the nati",
            <strong>{fmt(card.corrected_latitude)}′</strong>,
          ],
        ]}
      />
    </>
  );
}
