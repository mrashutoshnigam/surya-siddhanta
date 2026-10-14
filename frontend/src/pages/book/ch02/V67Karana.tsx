import { KVTable } from "../../../components/Tables";
import { dms } from "../ch01/scale";
import type { KaranaCard } from "./types";

/** ii.67-69 — the karana: half a tithi. Four are fixed, seven recur eight times a month. */
export function V67Karana({ card }: { card: KaranaCard }) {
  return (
    <>
      <KVTable
        rows={[
          ["Sun · Moon", `${dms(card.sun)} · ${dms(card.moon)}`],
          ["Moon − Sun", dms(card.elongation)],
          ["÷ 6°", `karana ${card.number} of 60 — ${card.half_of_tithi === 1 ? "first" : "second"} half of its tithi`],
          ["Name", <strong>{card.name}</strong>],
          ["Kind", card.kind],
        ]}
      />
      <p className="verse-note">
        Fixed: {card.fixed.join(", ")}. Recurring: {card.recurring.join(", ")}.
      </p>
    </>
  );
}
