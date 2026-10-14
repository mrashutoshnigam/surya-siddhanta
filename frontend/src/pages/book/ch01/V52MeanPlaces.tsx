import { useState } from "react";
import { GridTable } from "../../../components/Tables";
import { Slider } from "../../../components/VerseCard";
import { dms, grouped, meanLongitude, rashiOf } from "./scale";
import type { MeanPlacesCard } from "./types";

/**
 * i.52-54 — the mean places of all the planets at once.
 *
 * Drag the ahargana and the whole table moves: every longitude is the
 * v.35 proportion applied to that body's revolutions, with the epoch
 * offsets of v.57-58 for the Moon's apsis and node.
 */
export function V52MeanPlaces({ card, rashis }: { card: MeanPlacesCard; rashis: string[] }) {
  const [ahargana, setAhargana] = useState(Math.round(card.ahargana));

  const sighroccaFor = (planet: string) =>
    card.sighrocca.find((s) => s.planet === planet);

  return (
    <>
      <Slider
        label="Ahargana"
        value={ahargana}
        min={0}
        max={Math.round(card.ahargana) + 36525}
        step={1}
        suffix="days"
        onChange={setAhargana}
      />
      <p className="verse-note">
        {ahargana === Math.round(card.ahargana)
          ? "At the page's date."
          : `${grouped(ahargana - Math.round(card.ahargana))} days from the page's date.`}
      </p>

      <GridTable
        headers={["Body", "Mean longitude", "Sign", "Sighrocca"]}
        rows={card.bodies.map((body) => {
          const longitude = meanLongitude(
            body.bhagana,
            ahargana,
            card.civil_days_per_mahayuga,
            body.epoch,
            body.retrograde,
          );
          const sighra = sighroccaFor(body.planet);
          return [
            body.planet,
            dms(longitude),
            rashiOf(longitude, rashis),
            sighra
              ? dms(
                  meanLongitude(sighra.bhagana, ahargana, card.civil_days_per_mahayuga),
                )
              : "—",
          ];
        })}
      />
      <p className="verse-note">{card.note}</p>
    </>
  );
}
