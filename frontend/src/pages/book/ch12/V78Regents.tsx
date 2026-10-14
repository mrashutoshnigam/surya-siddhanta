import { KVTable } from "../../../components/Tables";
import type { RegentsCard } from "./types";

/**
 * xii.78-79 — the regents of day, month and year.
 *
 * Counting downward from Saturn, the fourth is the day's regent and the third
 * the year's; the month's is counted upward from the Moon. All follow from the
 * hora, a twenty-fourth of the day: 24, 720 and 8640 horas leave 3, 6 and 2
 * over when divided by seven.
 */
export function V78Regents({ card }: { card: RegentsCard }) {
  return (
    <>
      <KVTable
        rows={[
          ["Regent of the day", <strong key="d">{card.day}</strong>],
          ["Regent of the month", card.month],
          ["Regent of the year", card.year],
        ]}
      />
      <p className="ss-note">
        Horas of the day, from sunrise: {card.horas.join(", ")}.
      </p>
    </>
  );
}
