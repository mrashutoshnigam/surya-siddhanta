import { useState } from "react";
import { GridTable, KVTable } from "../../../components/Tables";
import { Picker, Slider } from "../../../components/VerseCard";
import { fmt } from "../ch01/scale";
import { useProbe } from "./probe";
import type { EpicycleAt, EpicyclesCard } from "./types";

/**
 * ii.34-38 — the pulsating epicycles.
 *
 * The epicycle is not a fixed size: it is the even-quadrant size at the
 * apsis line and the odd-quadrant size a quarter round, and swells between
 * them as the sine of the bhuja (v.38).
 */
export function V34Epicycles({ card }: { card: EpicyclesCard }) {
  const [body, setBody] = useState(card.rows[0].body);
  const [kendra, setKendra] = useState(card.sample_kendra);

  const row = card.rows.find((r) => r.body === body) ?? card.rows[0];
  const atSample = kendra === card.sample_kendra;
  const probed = useProbe<EpicycleAt>(
    atSample ? null : { card: "ii.34-38", body, kendra },
  );
  const at: EpicycleAt | null = atSample ? row.sample : probed;

  return (
    <>
      <GridTable
        headers={["Body", "Manda even", "Manda odd", "Sighra even", "Sighra odd"]}
        rows={card.rows.map((r) => [
          <span className={r.body === body ? "unit-selected" : undefined}>{r.body}</span>,
          r.manda_even,
          r.manda_odd,
          r.sighra_even ?? "—",
          r.sighra_odd ?? "—",
        ])}
      />
      <Picker
        label="Body"
        value={body}
        options={card.rows.map((r) => ({ value: r.body, label: r.body }))}
        onChange={setBody}
      />
      <Slider label="Anomaly (kendra)" value={kendra} min={0} max={360} step={1} suffix="°" onChange={setKendra} />
      {at === null ? (
        <p className="verse-note">computing…</p>
      ) : (
      <KVTable
        rows={[
          ["Bhuja · its sine", `${fmt(at.bhuja)}° · ${fmt(at.sin_bhuja)}`],
          [
            "Manda epicycle",
            <strong>
              {row.manda_even} + ({fmt(row.manda_odd - row.manda_even)}) × {fmt(at.sin_bhuja)} = {fmt(at.manda)}°
            </strong>,
          ],
          [
            "Sighra epicycle",
            at.sighra === null || row.sighra_even === null || row.sighra_odd === null ? (
              "none — the Sun and Moon have no conjunction"
            ) : (
              <strong>
                {row.sighra_even} + ({fmt(row.sighra_odd - row.sighra_even)}) × {fmt(at.sin_bhuja)} = {fmt(at.sighra)}°
              </strong>
            ),
          ],
        ]}
      />
      )}
    </>
  );
}
