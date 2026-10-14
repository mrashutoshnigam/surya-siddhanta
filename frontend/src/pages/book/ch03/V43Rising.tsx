import { useState } from "react";
import { GridTable } from "../../../components/Tables";
import { Slider } from "../../../components/VerseCard";
import { fmt } from "../ch01/scale";
import { useLastProbe } from "./probe";
import type { RisingCard, RisingResult } from "./types";

/**
 * iii.43-44 — the rising times of the signs.
 *
 * At Lanka (latitude 0) they are the text's 1670, 1795 and 1935 respirations;
 * at other latitudes each is lengthened or shortened by the cara. Figures are
 * respirations (asus): one degree of sidereal time is sixty.
 */
export function V43Rising({ card }: { card: RisingCard }) {
  const [latitude, setLatitude] = useState(card.latitude);
  const result = useLastProbe<RisingResult>({ card: "iii.43-44", latitude }, card);

  return (
    <>
      <Slider label="Latitude" value={latitude} min={-60} max={60} step={0.5} suffix="°" onChange={setLatitude} />
      <GridTable
        headers={["Sign", "At this latitude", "At Lanka (library)", "The text"]}
        rows={result.rows.map((r) => [r.rashi, fmt(r.asus), fmt(r.lanka_asus), String(r.text_asus)])}
      />
    </>
  );
}
