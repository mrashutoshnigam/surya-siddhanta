import { GridTable, KVTable } from "../../../components/Tables";
import { fmt } from "../ch01/scale";
import type { TimeCard } from "./types";

const NAMES: Record<string, string> = {
  nara: "Man-instrument (gnomon)",
  cakra: "Wheel",
  dhanus: "Arc",
  yashti: "Staff",
};

/**
 * xiii.20-24 — time from the instruments, and the clepsydra.
 *
 * The gnomon's shadow fixes the moment; the wheel and arc are read at the
 * altitude it implies and the staff at the chord that time would give, so the
 * four columns should agree. Only the gnomon is the text's own — the other
 * three come from Burgess's notes on the commentary, as does the bowl's
 * dimension. The clepsydra sinks once a ghati, sixty times a day and night.
 */
export function V20Time({ card }: { card: TimeCard }) {
  const c = card.clepsydra;
  return (
    <>
      {card.found && card.instruments ? (
        <div className="table-scroll">
          <GridTable
            headers={["Instrument", "Reading", "Altitude", "Ghatis since sunrise", "Ghatis to sunset", "Source"]}
            rows={card.instruments.map((t) => [
              NAMES[t.instrument] ?? t.instrument,
              `${fmt(t.reading)} ${t.reading_unit}`,
              `${fmt(t.sun_altitude_deg)}°`,
              fmt(t.ghatis_since_sunrise),
              fmt(t.ghatis_to_sunset),
              t.source === "verse" ? "verse" : "commentary",
            ])}
          />
        </div>
      ) : (
        <p className="ss-note">No time found for this shadow: {card.reason}</p>
      )}
      <KVTable
        title="The clepsydra"
        rows={[
          ["Day", `${fmt(c.day_ghatis)} ghatis — ${c.day_sinkings.sinkings} sinkings and ${fmt(c.day_sinkings.partial)} of the next`],
          ["Night", `${fmt(c.night_ghatis)} ghatis — ${c.night_sinkings.sinkings} sinkings and ${fmt(c.night_sinkings.partial)} of the next`],
        ]}
      />
    </>
  );
}
