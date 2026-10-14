import { useState } from "react";
import { KVTable } from "../../../components/Tables";
import { Slider } from "../../../components/VerseCard";
import { fmt } from "../ch01/scale";
import { useLastProbe } from "./probe";
import type { GnomonCard, GnomonResult } from "./types";

/** iii.5-8 — a twelve-digit gnomon's shadow, and the hypotenuse as root of the two squares. */
export function V05Gnomon({ card }: { card: GnomonCard }) {
  const [altitude, setAltitude] = useState(card.altitude);
  const result = useLastProbe<GnomonResult>({ card: "iii.5-8", altitude }, card);

  return (
    <>
      <Slider label="Sun's altitude" value={altitude} min={0} max={90} step={0.5} suffix="°" onChange={setAltitude} />
      <KVTable
        rows={[
          ["Gnomon", `${fmt(result.gnomon)} digits`],
          ["Shadow", result.shadow === null ? "none — the Sun is on the horizon" : `${fmt(result.shadow)} digits`],
          ["Hypotenuse", result.hypotenuse === null ? "—" : <strong>{fmt(result.hypotenuse)} digits</strong>],
        ]}
      />
    </>
  );
}
