import { KVTable } from "../../../components/Tables";
import { fmt } from "../ch01/scale";
import type { DaysCard } from "./types";

/**
 * xii.74 — the days of the gods, the manes and Brahma.
 *
 * The gods' day and night together are a sidereal year, the manes' a
 * synodic month, and Brahma's an aeon. The Surya Siddhanta puts the creation
 * a little under half an aeon before the Kali epoch, so any date in history
 * falls just past the middle of Brahma's present day.
 */
export function V74Days({ card }: { card: DaysCard }) {
  const b = card.brahma;
  return (
    <KVTable
      rows={[
        ["Day and night of the gods", `${fmt(card.day_of_the_gods)} days`],
        ["Day and night of the manes", `${fmt(card.day_of_the_manes)} days`],
        ["Day of Brahma (a kalpa)", `${b.kalpa_years.toLocaleString()} years`],
        ["Years since the creation", b.years_elapsed.toLocaleString()],
        ["Years remaining", b.years_remaining.toLocaleString()],
        ["Elapsed", <strong key="f">{fmt(b.fraction * 100)}% of Brahma's day</strong>],
      ]}
    />
  );
}
