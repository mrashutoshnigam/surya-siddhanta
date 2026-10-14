import { useState } from "react";
import { KVTable } from "../../../components/Tables";
import { Picker, Slider } from "../../../components/VerseCard";
import { fmt } from "../ch01/scale";
import { useProbe } from "./probe";
import type { BhujaKoti, BhujaKotiCard } from "./types";

/**
 * ii.29-30 — the bhuja and koti of an anomaly.
 *
 * The date's own kendras come with the payload; the slider probes any
 * anomaly through the library, so the quadrant rule can be walked round the
 * circle. In an odd quadrant the base-sine is taken from the part past, in
 * an even one from the part to come.
 */
export function V29BhujaKoti({ card }: { card: BhujaKotiCard }) {
  const [body, setBody] = useState(card.rows[0].body);
  const [which, setWhich] = useState<"manda" | "sighra">("manda");
  const [custom, setCustom] = useState<number | null>(null);

  const row = card.rows.find((r) => r.body === body) ?? card.rows[0];
  const own: BhujaKoti | null = which === "manda" ? row.manda : row.sighra;
  const noSighra = which === "sighra" && row.sighra === null;
  const probed = useProbe<BhujaKoti>(
    custom === null || noSighra ? null : { card: "ii.29-30", kendra: custom },
  );
  const shown = custom === null ? own : probed;

  return (
    <>
      <Picker
        label="Body"
        value={body}
        options={card.rows.map((r) => ({ value: r.body, label: r.body }))}
        onChange={(b) => {
          setBody(b);
          setCustom(null);
        }}
      />
      <Picker
        label="Anomaly"
        value={which}
        options={[
          { value: "manda", label: "of the apsis (manda)" },
          { value: "sighra", label: "of the conjunction (sighra)" },
        ]}
        onChange={(w) => {
          setWhich(w);
          setCustom(null);
        }}
      />
      {!noSighra && (
        <Slider
          label="Or any anomaly"
          value={custom ?? Math.round(own?.kendra ?? 0)}
          min={0}
          max={360}
          step={1}
          suffix="°"
          onChange={setCustom}
        />
      )}
      {noSighra ? (
        <p className="verse-note">
          The Sun and Moon have no conjunction (sighra) anomaly; only the apsis applies.
        </p>
      ) : shown ? (
        <KVTable
          rows={[
            ["Anomaly (kendra)", `${fmt(shown.kendra)}°`],
            ["Quadrant", `${shown.quadrant} (${shown.odd ? "odd" : "even"})`],
            ["Bhuja", `${fmt(shown.bhuja)}° — jya ${fmt(shown.bhuja_jya)}`],
            ["Koti", `${fmt(shown.koti)}° — jya ${fmt(shown.koti_jya)}`],
          ]}
        />
      ) : (
        <p className="verse-note">computing…</p>
      )}
    </>
  );
}
