import { useState } from "react";
import { KVTable } from "../../../components/Tables";
import { Slider } from "../../../components/VerseCard";
import { fmt } from "../ch01/scale";
import { useLastProbe } from "./probe";
import type { NoonShadow, NoonShadowCard } from "./types";

/** iii.21-23 — the noon zenith distance is latitude less declination; the shadow follows. */
export function V21NoonShadow({ card }: { card: NoonShadowCard }) {
  const [latitude, setLatitude] = useState(card.latitude);
  const [declination, setDeclination] = useState(card.declination);
  const result = useLastProbe<NoonShadow>(
    { card: "iii.21-23", latitude, declination },
    card,
  );

  return (
    <>
      <Slider label="Latitude" value={latitude} min={-90} max={90} step={0.5} suffix="°" onChange={setLatitude} />
      <Slider label="Declination" value={declination} min={-24} max={24} step={0.5} suffix="°" onChange={setDeclination} />
      <KVTable
        rows={[
          ["Zenith distance", `${fmt(result.zenith_distance)}°`],
          ["Altitude at noon", `${fmt(result.altitude)}°`],
          ["Shadow", result.shadow === null ? "none — the Sun is on the horizon" : <strong>{fmt(result.shadow)} digits</strong>],
          ["Hypotenuse", result.hypotenuse === null ? "—" : `${fmt(result.hypotenuse)} digits`],
        ]}
      />
    </>
  );
}
