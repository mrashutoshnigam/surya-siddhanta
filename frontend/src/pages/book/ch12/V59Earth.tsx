import { KVTable } from "../../../components/Tables";
import { fmt } from "../ch01/scale";
import type { EarthCard } from "./types";

const yoj = (n: number) => `${fmt(n)} yojanas`;

/**
 * xii.59-61 — the earth, its parallel and the polar day.
 *
 * The circumference is 1600 times the root of ten. The greatest declination,
 * turned into yojanas and taken from a quarter of the circumference, leaves
 * the parallel where the day first reaches sixty nadis. The corrected
 * circumference and desantara are SS i.60-61, which these verses rest on:
 * the place's distance from Lanka's meridian along its own parallel.
 */
export function V59Earth({ card }: { card: EarthCard }) {
  const polar = card.polar_day_limit;
  return (
    <>
      <KVTable
        title="The earth"
        rows={[
          ["Circumference (1600 × √10)", yoj(card.circumference)],
          [`Declination ${fmt(card.obliquity)}° in yojanas`, yoj(card.obliquity_yojanas)],
          ["Sixty-nadi day begins at", <strong>{fmt(polar.latitude)}° latitude</strong>],
          ["… yojanas from the equator", yoj(polar.yojanas_from_equator)],
          ["… yojanas from the pole", yoj(polar.yojanas_from_pole)],
        ]}
      />
      <KVTable
        title={`Your place (${fmt(card.latitude)}°, ${fmt(card.longitude)}°)`}
        rows={[
          ["Circumference of the parallel", yoj(card.corrected_circumference)],
          ["Desantara from Lanka's meridian", yoj(card.desantara_yojanas)],
          ["Moon's daily motion", `${fmt(card.moon_daily_arcmin)}′`],
          ["Longitude correction to her place", `${fmt(card.moon_correction_arcmin)}′`],
        ]}
      />
      <p className="ss-note">
        The latitude cancels out of the correction: it depends only on the difference of
        longitude. Negative means east of the meridian, where the day comes earlier.
      </p>
    </>
  );
}
