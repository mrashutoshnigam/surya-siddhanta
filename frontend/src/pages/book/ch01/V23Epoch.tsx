import { useState } from "react";
import { KVTable } from "../../../components/Tables";
import { Picker } from "../../../components/VerseCard";
import { fmt, grouped } from "./scale";
import type { EpochCard } from "./types";

type Reckoning = "days" | "years";

/**
 * i.23-24 — the Kali epoch and the time elapsed to the page's date.
 *
 * The one control is which way round to read the interval: as the count
 * of civil days the rest of the chapter works in (the ahargana), or as
 * the sidereal years that count comes to.
 */
export function V23Epoch({ card }: { card: EpochCard }) {
  const [reckoning, setReckoning] = useState<Reckoning>("days");

  const headline =
    reckoning === "days"
      ? `${grouped(card.ahargana)} civil days since the epoch`
      : `${fmt(card.kali_years_elapsed)} sidereal years since the epoch`;

  return (
    <>
      <Picker
        label="Read the interval as"
        value={reckoning}
        options={[
          { value: "days", label: "Civil days (ahargana)" },
          { value: "years", label: "Sidereal years" },
        ]}
        onChange={setReckoning}
      />
      <p className="verse-readout">
        <strong>{headline}</strong>
      </p>

      <KVTable
        rows={[
          ["Kali epoch", `JD ${card.kali_epoch_jd} — ${card.kali_epoch_date}`],
          ["This date", `JD ${card.jd} (Ujjain mean time)`],
          ["Ahargana", `${grouped(card.ahargana)} days`],
          ["Years elapsed", fmt(card.kali_years_elapsed)],
          ["Kali era year", grouped(card.kali_era_year)],
          ["Through the Kali Age", `${(card.kali_fraction_elapsed * 100).toFixed(4)} %`],
          [
            "Through the Age, from the epoch",
            `${(card.yuga_elapsed_fraction * 100).toFixed(4)} %`,
          ],
        ]}
      />
      <p className="verse-note">{card.note}</p>
    </>
  );
}
