import { useState } from "react";
import { GridTable, KVTable } from "../../../components/Tables";
import { Slider } from "../../../components/VerseCard";
import { fmt, grouped } from "./scale";
import type { YugasCard } from "./types";

/**
 * i.15-22 — the four Ages, the Age and the Aeon.
 *
 * The slider walks a position through one Age and names which of the four
 * that position falls in, by the 4:3:2:1 proportion the verses give. It
 * starts at 3,888,000 years, where the Kali Age — and the epoch of the
 * whole system — begins.
 */
export function V15Yugas({ card }: { card: YugasCard }) {
  const [yearsElapsed, setYearsElapsed] = useState(3_888_000);

  let running = 0;
  const rows = card.ages.map((age) => {
    const start = running;
    running += age.years;
    const within = yearsElapsed >= start && yearsElapsed < running;
    return {
      age,
      start,
      end: running,
      within,
      cells: [
        <span className={within ? "unit-selected" : undefined}>{age.name}</span>,
        grouped(age.years),
        `${grouped(start)} – ${grouped(running)}`,
        within ? `${grouped(yearsElapsed - start)} elapsed` : "",
      ],
    };
  });
  const current = rows.find((r) => r.within) ?? rows[rows.length - 1];

  return (
    <>
      <Slider
        label="Years elapsed in the Age"
        value={yearsElapsed}
        min={0}
        max={card.mahayuga_years}
        step={1000}
        suffix="years"
        onChange={setYearsElapsed}
      />
      <p className="verse-readout">
        That falls in the <strong>{current.age.name}</strong> Age,{" "}
        {grouped(yearsElapsed - current.start)} years in, with{" "}
        {grouped(current.end - yearsElapsed)} to run.
      </p>

      <GridTable
        headers={["Age", "Years", "From – to", "Position"]}
        rows={rows.map((r) => r.cells)}
      />

      <KVTable
        title="The Age and the Aeon"
        rows={[
          ["An Age (mahayuga)", `${grouped(card.mahayuga_years)} years`],
          [
            "An Aeon (kalpa)",
            `${grouped(card.kalpa_years)} years = ${grouped(card.mahayugas_per_kalpa)} Ages`,
          ],
          ["Civil days in an Age", grouped(card.civil_days_per_mahayuga)],
          ["Sidereal days in an Age", grouped(card.sidereal_days_per_mahayuga)],
          ["Lunar months in an Age", grouped(card.lunar_months_per_mahayuga)],
          ["Civil days in an Aeon", grouped(card.civil_days_per_kalpa)],
          ["Sidereal year", `${fmt(card.sidereal_year_days)} days`],
        ]}
      />
    </>
  );
}
