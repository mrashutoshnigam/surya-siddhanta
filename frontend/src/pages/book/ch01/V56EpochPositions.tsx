import { useState } from "react";
import { GridTable, KVTable } from "../../../components/Tables";
import { Picker } from "../../../components/VerseCard";
import { fmt, grouped } from "./scale";
import type { EpochPositionsCard } from "./types";

type Era = "kali" | "creation";

/**
 * i.56-58 — reckoning from a later epoch, and the positions at the epoch.
 *
 * The toggle is v.56 itself: the same instant counted from the end of
 * creation, as the text does, or from the Kali epoch, as everything else
 * in this module does. The difference between the two is one constant.
 */
export function V56EpochPositions({ card }: { card: EpochPositionsCard }) {
  const [era, setEra] = useState<Era>("kali");

  return (
    <>
      <Picker
        label="Reckon from"
        value={era}
        options={[
          { value: "kali", label: "The Kali epoch" },
          { value: "creation", label: "The end of creation" },
        ]}
        onChange={setEra}
      />

      <KVTable
        rows={
          era === "kali"
            ? [
                ["Epoch", "Midnight, Feb 17–18, 3102 BCE (JD 588465.5)"],
                ["Days already elapsed at it", grouped(card.civil_days_creation_to_kali)],
                ["What v.56 allows", "dropping those days, and counting from here"],
              ]
            : [
                ["Epoch", "The end of creation"],
                ["Years to the Kali epoch", grouped(card.years_creation_to_kali)],
                ["= quarter-Ages", grouped(card.quarter_ages)],
                ["Civil days to the Kali epoch", grouped(card.civil_days_creation_to_kali)],
                ["In Ages", fmt(card.years_creation_to_kali / 4_320_000)],
              ]
        }
      />

      <GridTable
        headers={["Body", "Apsis at the epoch", "Node at the epoch"]}
        rows={card.rows.map((r) => [r.planet, r.mandocca_dms, r.node_dms ?? "—"])}
      />
      <p className="verse-note">
        v.57 puts every planet and every conjunction at the first of Aries at the end
        of the Golden Age, which is why only the apsides and nodes need carrying.
      </p>
      <p className="verse-note">{card.note}</p>
    </>
  );
}
