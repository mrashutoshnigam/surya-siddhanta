import { GridTable, KVTable } from "../../../components/Tables";
import { fmt } from "../ch01/scale";
import type { AsterismsCard } from "./types";

/**
 * xiv.15-16 — the months and their asterisms.
 *
 * Twelve months from Kartika take the twenty-seven asterisms from Krittika,
 * two by two; the fifth, the last but one and the last take three. Each month
 * holds its own namesake asterism. The Moon's place is read at the date.
 */
export function V15Months({ card }: { card: AsterismsCard }) {
  return (
    <>
      <KVTable
        rows={[
          ["Moon's longitude", `${fmt(card.moon_longitude)}°`],
          ["Her asterism", card.moon_asterism],
          ["Belonging to the month", <strong key="m">{card.moon_month}</strong>],
        ]}
      />
      <div className="table-scroll">
        <GridTable
          headers={["Month", "Asterisms", "Namesake"]}
          rows={card.months.map((m) => [
            m.month === card.moon_month ? <strong key={m.month}>{m.month}</strong> : m.month,
            m.asterisms.join(", "),
            m.namesake,
          ])}
        />
      </div>
    </>
  );
}
