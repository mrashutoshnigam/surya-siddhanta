import { KVTable } from "../../../components/Tables";
import { fmt } from "../ch01/scale";
import type { ContactsCard } from "./types";

/**
 * v.15-17 — the half-duration, corrected for the parallax at the ends.
 *
 * The parallax in longitude differs at contact, middle and separation, so the
 * eclipse lasts longer on one side and shorter on the other. With the signed
 * lambana, an event is seen at its time plus lambana over the relative speed;
 * the half-duration of each side moves by the change of lambana across it.
 * That one rule covers the verses' three cases (v.15, v.16 and the two
 * hemispheres of v.17).
 */
export function V15Contacts({ card }: { card: ContactsCard }) {
  if (!card.is_eclipse) {
    return <p className="ss-note">There is no eclipse here at this new moon, so nothing to correct.</p>;
  }
  return (
    <>
    <KVTable
      rows={[
        ["Hemisphere of the Sun", `${card.hemisphere} (hour angle ${fmt(card.hour_angle)}°)`],
        [
          "Lambana at contact, middle, separation",
          `${fmt(card.lambana_contact)}′, ${fmt(card.lambana_middle)}′, ${fmt(card.lambana_separation)}′`,
        ],
        ["Half-duration before correction", `${fmt(card.half_duration_min)} min`],
        [
          "Contact side",
          <strong>
            {fmt(card.contact_half_min)} min ({card.contact_adjust_min >= 0 ? "+" : ""}{fmt(card.contact_adjust_min)})
          </strong>,
        ],
        [
          "Separation side",
          <strong>
            {fmt(card.separation_half_min)} min ({card.separation_adjust_min >= 0 ? "+" : ""}{fmt(card.separation_adjust_min)})
          </strong>,
        ],
      ]}
    />
    <p className="ss-note">
      The lambana at the middle differs from the one at v.8-9 because it is taken at the
      corrected moment of the eclipse, the first pass of the repetition v.9 asks for.
    </p>
    </>
  );
}
