import { KVTable } from "../../../components/Tables";
import { fmt } from "../ch01/scale";
import type { IlluminationCard } from "./types";

/**
 * x.9 — the illuminated part.
 *
 * The elongation in minutes, divided by nine hundred, is the lit part in
 * digits of the twelve-digit disc: linear in the elongation, as the verse
 * states, so the library's fraction is this over twelve. Past half a
 * revolution v.16 applies the same rule to the elongation taken from a full
 * circle. The versine width is the bhashya's refinement, the width of the
 * crescent along the Moon's axis.
 */
export function V09Illumination({ card }: { card: IlluminationCard }) {
  return (
    <KVTable
      rows={[
        ["Elongation", `${fmt(card.elongation)}° — ${card.phase}, ${card.paksha}`],
        ["Used in the rule", `${fmt(card.reflected_elongation)}° = ${fmt(card.minutes)}′`],
        ["Lit part", <strong>{fmt(card.lit_digits)} of 12 digits</strong>],
        ["As a fraction of the disc", fmt(card.fraction)],
        ["Library fraction", fmt(card.library_fraction)],
        [
          "Width along the axis (versine)",
          `${fmt(card.width_arcmin)}′ of a ${fmt(2 * card.moon_radius_arcmin)}′ disc`,
        ],
      ]}
    />
  );
}
