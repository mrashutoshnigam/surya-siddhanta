import { KVTable } from "../../../components/Tables";
import { dms, fmt } from "../ch01/scale";
import { fmtDate } from "../dates";
import type { ClassificationCard } from "./types";

/**
 * vii.19-22 — encounter or conjunction.
 *
 * When the interval is under a degree the star-planets are in encounter
 * (yuddha), "ray-obliteration"; farther apart they are in conjunction
 * (samagama). The victor is the one to the north. The verses add further
 * tests of brightness, size and colour (v.20-22) that the library does not
 * model, so the victor here is decided by latitude alone.
 */
export function V19Classification({ card }: { card: ClassificationCard }) {
  if (!card.found) {
    return <p className="ss-note">There is no conjunction of this pair within the search window.</p>;
  }
  return (
    <KVTable
      rows={[
        ["Conjunction", fmtDate(card.date)],
        ["In longitude", dms(card.longitude)],
        ["Interval", `${fmt(card.separation_deg)}° (limit ${fmt(card.limit_deg)}°)`],
        ["This is", <strong>{card.type === "yuddha" ? "an encounter (yuddha)" : "a conjunction (samagama)"}</strong>],
        ["Planet to the north", card.north_planet],
        ["Victor", card.winner ? <strong>{card.winner}</strong> : "none — no encounter"],
      ]}
    />
  );
}
