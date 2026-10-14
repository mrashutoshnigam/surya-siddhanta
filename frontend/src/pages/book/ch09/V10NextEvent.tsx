import { KVTable } from "../../../components/Tables";
import { fmt } from "../ch01/scale";
import { fmtDate } from "../dates";
import type { NextEventCard } from "./types";

/**
 * ix.10-11 — the time to the next event.
 *
 * The shortfall from the limit, divided by the difference of the daily
 * motions (their sum when retrograding), is the number of days to the setting
 * or rising. One step is a straight-line guess; the library scans day by day
 * and bisects, so the two differ when the rate of closing is changing.
 */
export function V10NextEvent({ card }: { card: NextEventCard }) {
  return (
    <>
      <KVTable
        rows={[
          ["Event looked for", card.event],
          ["Elongation, limit", `${fmt(card.elongation)}°, ${card.threshold}°`],
          ["Shortfall", `${fmt(Math.abs(card.shortfall_arcmin))}′`],
          ["Daily motions, planet and Sun", `${fmt(card.planet_motion)}°, ${fmt(card.sun_motion)}°`],
          ["Rate the elongation changes by", `${fmt(card.closing_rate)}°/day`],
          [
            "By the verse, in",
            card.hand_days !== null && card.hand_date ? (
              <strong>
                {fmt(card.hand_days)} days — {fmtDate(card.hand_date)}
              </strong>
            ) : (
              "no one-step answer"
            ),
          ],
          [
            "Library",
            card.library ? <strong>{fmtDate(card.library.date)}</strong> : "none within 800 days",
          ],
          ["Difference", card.days_apart !== null ? `${fmt(card.days_apart)} days` : "—"],
        ]}
      />
      {card.hand_days === null && (
        <p className="ss-note">
          The elongation is moving the wrong way for one step to reach the {card.event}: the
          planet has first to pass the Sun (or turn), so the verse's single division does not
          apply and the process has to be repeated.
        </p>
      )}
    </>
  );
}
