import { KVTable } from "../../../components/Tables";
import { fmt } from "../ch01/scale";
import type { DirectionCard } from "./types";

/**
 * ix.2-3 — which way the planet is heading.
 *
 * Mars, Jupiter and Saturn, and Mercury or Venus while retrograding, go to
 * their setting in the west when their longitude is greater than the Sun's
 * and to their rising in the east when it is less. The swift Mercury and
 * Venus do the opposite. A planet already inside its limit is lost, and the
 * event it heads for is the rising on the far side of the Sun.
 */
export function V02Direction({ card }: { card: DirectionCard }) {
  return (
    <>
      <KVTable
        rows={[
          [`${card.planet}, longitude less the Sun's`, `${fmt(card.elongation)}°`],
          ["Longitude is", card.greater_than_sun ? "greater than the Sun's" : "less than the Sun's"],
          ["Motion", card.retrograde ? "retrograde" : "direct"],
          ["Rule of v.2-3", card.rule === "slow" ? "slow planet (or retrograding)" : "swift planet"],
          ["Heading for", <strong>{card.event} in the {card.horizon}</strong>],
        ]}
      />
      {!card.visible && (
        <p className="ss-note">
          The planet is inside its limit already, so it is lost in the Sun's rays; the next event
          is its rising after it has passed him.
        </p>
      )}
    </>
  );
}
