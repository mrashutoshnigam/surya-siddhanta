import { useState } from "react";
import { GridTable } from "../../../components/Tables";
import { Picker, Slider } from "../../../components/VerseCard";
import { convertUnits, fmt, humanSeconds } from "./scale";
import type { TimeUnitsCard } from "./types";

/**
 * i.11-13 — the divisions of time, as a converter.
 *
 * Pick a chain, pick a unit, drag the amount: every other unit in the
 * chain restates the same span. A conversion is the ratio of two lengths
 * in seconds, both of which came from ch01_mean_motions.py, so nothing is
 * recomputed here that the library does not already state.
 */
export function V11TimeUnits({ card }: { card: TimeUnitsCard }) {
  const [chainKey, setChainKey] = useState(card.chains[0].key);
  const chain = card.chains.find((c) => c.key === chainKey) ?? card.chains[0];
  const [unit, setUnit] = useState(chain.units[chain.units.length - 2].unit);
  const [amount, setAmount] = useState(16);

  // Changing chain can strand the selected unit; fall back to its first.
  const selected = chain.units.find((u) => u.unit === unit) ?? chain.units[0];
  const totalSeconds = amount * selected.seconds;

  const rows = chain.units.map((u) => [
    <span className={u.unit === selected.unit ? "unit-selected" : undefined}>
      {u.unit}
      {u.alias ? <em> ({u.alias})</em> : null}
    </span>,
    fmt(convertUnits(amount, selected.seconds, u.seconds)),
    fmt(u.seconds),
    u.in_ss_text ? "the text" : "commentary",
  ]);

  const sentence = chain.units
    .filter((u) => u.next && u.per_next)
    .map((u) => `${fmt(u.per_next as number)} ${u.unit} = 1 ${u.next}`)
    .join("  ·  ");

  return (
    <>
      <Picker
        value={chainKey}
        options={card.chains.map((c) => ({ value: c.key, label: c.label }))}
        onChange={(key) => {
          const next = card.chains.find((c) => c.key === key);
          setChainKey(key);
          if (next) setUnit(next.units[Math.max(0, next.units.length - 2)].unit);
        }}
      />
      <Picker
        label="Unit"
        value={selected.unit}
        options={chain.units.map((u) => ({ value: u.unit, label: u.alias ?? u.unit }))}
        onChange={setUnit}
      />
      <Slider
        label={`Amount in ${selected.unit}`}
        value={amount}
        min={0}
        max={120}
        step={0.5}
        onChange={setAmount}
      />

      <GridTable
        headers={["Unit", `Equal to ${fmt(amount)} ${selected.unit}`, "Seconds each", "Source"]}
        rows={rows}
      />

      <p className="verse-readout">
        {fmt(amount)} {selected.unit} = <strong>{humanSeconds(totalSeconds)}</strong> —{" "}
        {fmt(totalSeconds / 86400)} of a day
      </p>
      <p className="verse-note">{sentence}</p>
      <p className="verse-note">{card.note}</p>
    </>
  );
}
