import { KVTable } from "../../../components/Tables";
import { dms, fmt } from "../ch01/scale";
import type { TithiCard } from "./types";

/** ii.66 — the lunar day: the Moon's elongation from the Sun, divided by 12°. */
export function V66Tithi({ card }: { card: TithiCard }) {
  return (
    <KVTable
      rows={[
        ["Sun · Moon", `${dms(card.sun)} · ${dms(card.moon)}`],
        ["Moon − Sun", dms(card.elongation)],
        ["÷ 12°", `tithi ${card.number} of 30`],
        ["Half-month", card.paksha === "shukla" ? "bright (shukla)" : "dark (krishna)"],
        ["Name", <strong>{card.name}</strong>],
        ["Elapsed", `${fmt(card.fraction * 100)}%`],
      ]}
    />
  );
}
