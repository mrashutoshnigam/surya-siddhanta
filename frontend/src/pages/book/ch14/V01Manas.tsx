import { GridTable } from "../../../components/Tables";
import type { ManasCard } from "./types";

/**
 * xiv.1-2 — the nine modes of time.
 *
 * Verse 2 divides them: four are used in practice (solar, civil, lunar,
 * sidereal), Jupiter's names the years of his cycle, and the rest are never
 * used. The last column is the chosen date expressed in each.
 */
export function V01Manas({ card }: { card: ManasCard }) {
  return (
    <div className="table-scroll">
      <GridTable
        headers={["Mode", "Unit", "In practice", "The date in this mode"]}
        rows={card.manas.map((m) => [
          <span key={m.key}>
            <strong>{m.iast}</strong> ({m.english})
          </span>,
          m.unit,
          m.practical ? "yes" : "no",
          m.description,
        ])}
      />
    </div>
  );
}
