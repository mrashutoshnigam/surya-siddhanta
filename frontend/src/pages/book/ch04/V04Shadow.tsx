import { KVTable } from "../../../components/Tables";
import { fmt } from "../ch01/scale";
import type { ShadowCard } from "./types";

/** iv.4-5 — the earth's shadow at the Moon's distance, by the suci rule. */
export function V04Shadow({ card }: { card: ShadowCard }) {
  return (
    <KVTable
      rows={[
        ["Earth's diameter", `${fmt(card.earth_yojana)} yojanas`],
        ["Sun's less earth's", `${fmt(card.difference)} yojanas`],
        ["× Moon ÷ Sun", `${fmt(card.correction)} yojanas`],
        ["Shadow, in yojanas", `${fmt(card.shadow_yojana)}`],
        ["Shadow, in minutes", <strong>{fmt(card.shadow_arcmin)}′</strong>],
        ["Library", `${fmt(card.library_arcmin)}′`],
      ]}
    />
  );
}
