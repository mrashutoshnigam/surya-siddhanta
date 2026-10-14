import { KVTable } from "../../../components/Tables";
import { fmt } from "../ch01/scale";
import type { DirectionsCard } from "./types";

/** North/south word for a north-positive angle. */
function side(value: number): string {
  return value >= 0 ? "north" : "south";
}

/**
 * vi.4-9 — contact, separation and the deflection.
 *
 * A lunar eclipse begins on the east and ends on the west; a solar one the
 * reverse (v.4). The deflection (valana, from SS Ch.4 v.24-25) is laid off
 * in its own direction at contact in a lunar eclipse and reversed at
 * separation; a solar eclipse does the contrary (v.5). Which way the line
 * leans follows the latitude by v.9.
 */
export function V04Directions({ card }: { card: DirectionsCard }) {
  return (
    <KVTable
      rows={[
        ["Contact on the", <strong>{card.contact_limb}</strong>],
        ["Separation on the", <strong>{card.separation_limb}</strong>],
        [
          "Valana (ayana + aksha)",
          `${fmt(Math.abs(card.valana))}° ${card.valana_direction} = ${fmt(card.ayana_valana)}° + ${fmt(card.aksha_valana)}°`,
        ],
        ["Valana laid off at contact", `${fmt(Math.abs(card.contact_valana))}° ${side(card.contact_valana)}`],
        ["Valana laid off at separation", `${fmt(Math.abs(card.separation_valana))}° ${side(card.separation_valana)}`],
        ["Latitude of the path", `${fmt(Math.abs(card.latitude))}′ ${card.latitude_direction}`],
        ["Latitude is drawn", card.latitude_drawn],
        [
          "Deflection laid to the",
          `${card.deflection_laid} (valana and latitude ${card.same_direction ? "agree" : "differ"})`,
        ],
      ]}
    />
  );
}
