import { KVTable } from "../../../components/Tables";
import { dms, fmt } from "../ch01/scale";
import { fmtDate } from "../dates";
import type { PositionCard } from "./types";

/**
 * viii.1-9 applied — where the chosen star stands on the date.
 *
 * The catalog position is sidereal and fixed; the SS ayanamsha of the date
 * turns it to a tropical longitude, which gives the right ascension and
 * declination. The rising and setting are the library's, not a verse's: the
 * star's own equatorial coordinates against the horizon of the place.
 */
export function V09Position({ card }: { card: PositionCard }) {
  return (
    <KVTable
      rows={[
        [`${card.name} — ${card.star}`, `regent ${card.deity}`],
        ["Sidereal longitude, latitude", `${dms(card.sidereal_lon)}, ${fmt(card.sidereal_lat)}°`],
        ["Ayanamsha of the date", `${fmt(card.ayanamsha)}°`],
        ["Tropical longitude", dms(card.tropical_lon)],
        ["Right ascension", dms(card.right_ascension)],
        ["Declination", <strong>{fmt(card.declination)}°</strong>],
        ["Lies in the bhoga of", card.bhoga_of],
        [
          "Rises (library)",
          card.circumpolar
            ? "never sets here"
            : card.never_visible
              ? "never rises here"
              : card.rise
                ? fmtDate(card.rise)
                : "—",
        ],
        ["Sets (library)", card.set ? fmtDate(card.set) : "—"],
      ]}
    />
  );
}
