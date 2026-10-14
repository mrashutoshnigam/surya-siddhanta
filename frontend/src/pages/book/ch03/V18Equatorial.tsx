import { useState } from "react";
import { GridTable, KVTable } from "../../../components/Tables";
import { Slider } from "../../../components/VerseCard";
import { dms, fmt } from "../ch01/scale";
import { useLastProbe } from "./probe";
import type { Equatorial, EquatorialCard } from "./types";

/** iii.18-20 — declination and right ascension, for each body and for a free longitude. */
export function V18Equatorial({ card }: { card: EquatorialCard }) {
  const [longitude, setLongitude] = useState(card.rows[0].tropical);
  const result = useLastProbe<Equatorial>(
    { card: "iii.18-20", longitude },
    card.rows[0],
  );

  return (
    <>
      <GridTable
        headers={["Body", "Tropical longitude", "Declination", "Right ascension"]}
        rows={card.rows.map((r) => [
          r.body,
          dms(r.tropical),
          `${fmt(Math.abs(r.declination))}° ${r.direction}`,
          dms(r.right_ascension),
        ])}
      />
      <Slider label="Any longitude (tropical)" value={longitude} min={0} max={360} step={1} suffix="°" onChange={setLongitude} />
      <KVTable
        rows={[
          ["Declination", `${fmt(Math.abs(result.declination))}° ${result.direction}`],
          ["Right ascension", dms(result.right_ascension)],
        ]}
      />
    </>
  );
}
