import { KVTable } from "../../../components/Tables";
import { fmt } from "../ch01/scale";
import { fmtDate } from "../dates";
import type { RiseSetCard } from "./types";

/**
 * x.2-5 — the Moon's rising and setting.
 *
 * The verses find how long after the Sun she sets (or before him she rises)
 * by repeating the interval in respirations. That method is not laid out;
 * these are the library's next moonrise and moonset after the date, found by
 * scanning the Moon's altitude at the place.
 */
export function V02RiseSet({ card }: { card: RiseSetCard }) {
  return (
    <KVTable
      rows={[
        ["Place", `${fmt(card.latitude)}°, ${fmt(card.longitude)}°`],
        ["Next moonrise (library)", card.rise ? fmtDate(card.rise) : "none within two days"],
        ["Next moonset (library)", card.set ? fmtDate(card.set) : "none within two days"],
      ]}
    />
  );
}
