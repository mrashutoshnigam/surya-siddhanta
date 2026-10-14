import { useState } from "react";
import { GridTable, KVTable } from "../../../components/Tables";
import { Picker, Slider } from "../../../components/VerseCard";
import { dms, fmt, grouped, norm360, rashiOf } from "./scale";
import type { ApsidesCard } from "./types";

/**
 * i.41-42 (the apsides) and i.43-44 (the nodes).
 *
 * One component for both, because the two verses state the same thing of
 * two different points: a count of revolutions in an Aeon, a position at
 * the Kali epoch, and a direction. Only the wording differs, which the
 * `kind` prop carries.
 *
 * The slider moves days away from the page's date. These points move so
 * slowly — 39 revolutions in an Aeon for Saturn's apsis — that a decade
 * of slider barely stirs the arc-seconds, which is the verse's own point.
 */
export function V41OrbitPoints({
  card,
  kind,
  rashis,
}: {
  card: ApsidesCard;
  kind: "apsis" | "node";
  rashis: string[];
}) {
  const [planet, setPlanet] = useState(card.rows[0].planet);
  const [offsetDays, setOffsetDays] = useState(0);

  const selected = card.rows.find((r) => r.planet === planet) ?? card.rows[0];
  const ahargana = card.ahargana + offsetDays;
  const at = (motion: number, epoch: number) => norm360(epoch + motion * ahargana);
  const longitude = at(selected.daily_motion, selected.epoch_longitude);

  return (
    <>
      <Picker
        label="Body"
        value={planet}
        options={card.rows.map((r) => ({ value: r.planet, label: r.planet }))}
        onChange={setPlanet}
      />
      <Slider
        label="Days from this date"
        value={offsetDays}
        min={-36525}
        max={36525}
        step={365}
        suffix="days"
        onChange={setOffsetDays}
      />

      <KVTable
        rows={[
          [`${selected.planet}'s ${kind}`, <strong>{dms(longitude)}</strong>],
          ["in the signs", rashiOf(longitude, rashis)],
          [
            "revolutions",
            `${grouped(selected.revolutions)} in an ${selected.per}${
              kind === "node" ? ", retrograde" : ""
            }`,
          ],
          ["motion", `${fmt(selected.daily_motion * 36525)}° per century`],
          ["at the Kali epoch", dms(selected.epoch_longitude)],
        ]}
      />

      <GridTable
        headers={["Body", "Revolutions", "Per", "At the epoch", `${kind === "node" ? "Node" : "Apsis"} now`, "Sign"]}
        rows={card.rows.map((r) => {
          const value = at(r.daily_motion, r.epoch_longitude);
          return [
            <span className={r.planet === selected.planet ? "unit-selected" : undefined}>
              {r.planet}
            </span>,
            grouped(r.revolutions),
            r.per,
            dms(r.epoch_longitude),
            dms(value),
            rashiOf(value, rashis),
          ];
        })}
      />
      <p className="verse-note">
        The Moon's {kind} is reckoned per Age (v.33); the rest per Aeon, a thousand
        times slower.
      </p>
    </>
  );
}
