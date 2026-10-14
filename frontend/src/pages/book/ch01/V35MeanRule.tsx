import { useState } from "react";
import { GridTable, KVTable } from "../../../components/Tables";
import { Picker, Slider } from "../../../components/VerseCard";
import { dms, fmt, grouped, meanLongitude, rashiOf } from "./scale";
import type { MeanRuleCard } from "./types";

/**
 * i.35-37 — the rule for a mean place, worked step by step.
 *
 * The slider moves the ahargana away from the page's date so the four
 * terms of the proportion can be watched changing: revolutions, turns
 * elapsed, the fraction of a turn left over, and the longitude it makes.
 */
export function V35MeanRule({ card, rashis }: { card: MeanRuleCard; rashis: string[] }) {
  const [body, setBody] = useState("Sun");
  const [ahargana, setAhargana] = useState(Math.round(card.ahargana));

  const revolutions = card.bhagana[body] ?? card.bhagana.Sun;
  const turns = (revolutions * ahargana) / card.civil_days_per_mahayuga;
  const fraction = turns - Math.floor(turns);
  const longitude = meanLongitude(revolutions, ahargana, card.civil_days_per_mahayuga);

  return (
    <>
      <p className="verse-formula">{card.formula}</p>

      <Picker
        label="Body"
        value={body}
        options={Object.keys(card.bhagana).map((name) => ({
          value: name,
          label: name.replace("_", " "),
        }))}
        onChange={setBody}
      />
      <Slider
        label="Ahargana"
        value={ahargana}
        min={0}
        max={Math.round(card.ahargana) + 36525}
        step={1}
        suffix="days"
        onChange={setAhargana}
      />

      <KVTable
        title="The proportion, term by term"
        rows={[
          ["Revolutions in an Age", grouped(revolutions)],
          ["× ahargana", grouped(ahargana)],
          ["÷ civil days in an Age", grouped(card.civil_days_per_mahayuga)],
          ["= turns elapsed", fmt(turns)],
          ["fraction of a turn", fmt(fraction)],
          ["× 360°", <strong>{dms(longitude)}</strong>],
          ["in the signs", rashiOf(longitude, rashis)],
        ]}
      />

      <GridTable
        headers={["Body", "Turns elapsed on this date", "Fraction", "Mean longitude"]}
        rows={card.worked.map((w) => [
          <span className={w.body === body ? "unit-selected" : undefined}>{w.body}</span>,
          fmt(w.turns_elapsed),
          fmt(w.fraction_of_turn),
          w.longitude_dms,
        ])}
      />
      <p className="verse-note">
        The table holds the page's date; the slider above moves only this card.
        Sidereal year: {fmt(card.sidereal_year_days)} days.
      </p>
    </>
  );
}
