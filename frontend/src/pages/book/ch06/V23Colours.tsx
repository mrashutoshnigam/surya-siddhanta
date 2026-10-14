import { GridTable, KVTable } from "../../../components/Tables";
import { fmt } from "../ch01/scale";
import type { ColoursCard } from "./types";

/**
 * vi.23 — the colours.
 *
 * The part obscured is dusky when less than half, black when more; it is
 * dark copper while emerging, and tawny at total obscuration.
 */
export function V23Colours({ card }: { card: ColoursCard }) {
  return (
    <>
      <GridTable headers={["Phase", "Colour"]} rows={card.scheme.map((s) => [s.phase, s.colour])} />
      <KVTable
        rows={[
          ["Magnitude at the middle", fmt(card.magnitude)],
          ["Colour then", <strong>{card.at_maximum ?? "no eclipse"}</strong>],
        ]}
      />
    </>
  );
}
