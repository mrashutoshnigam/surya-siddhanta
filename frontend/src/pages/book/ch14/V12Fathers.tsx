import { KVTable } from "../../../components/Tables";
import { fmt } from "../ch01/scale";
import { fmtDate } from "../dates";
import type { FathersCard } from "./types";

/**
 * xiv.12-14 — the tithi, and the day of the Fathers.
 *
 * A lunar month is one day and night of the Fathers. The new moon is their
 * midday and the full moon their midnight, so their hour is twelve plus the
 * elongation over fifteen.
 */
export function V12Fathers({ card }: { card: FathersCard }) {
  return (
    <KVTable
      rows={[
        ["Elongation (Moon − Sun)", `${fmt(card.elongation)}°`],
        ["Tithi", `${card.tithi} — ${card.tithi_name}, ${card.paksha} paksha`],
        ["Hour of the Fathers' day", `${fmt(card.hour)} of 24 (${card.phase})`],
        ["Ghati of their day", fmt(card.ghati)],
        ["Their next midday (new moon)", fmtDate(card.next_noon)],
        ["Their next midnight (full moon)", fmtDate(card.next_midnight)],
        ["Their day and night", `${fmt(card.month_days)} of our days`],
      ]}
    />
  );
}
