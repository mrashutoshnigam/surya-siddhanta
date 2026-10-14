import { GridTable, KVTable } from "../../../components/Tables";
import { fmt } from "../ch01/scale";
import { fmtDate } from "../dates";
import type { SankrantisCard } from "./types";

/**
 * xiv.7-11 — the solar year.
 *
 * The Sun's twelve entries into the signs, with the auspicious time (the
 * punyakala) on each side, the ayanas and visuvats among them, and the six
 * seasons of two signs. The punyakala uses the Sun's mean disk, so it varies
 * with his daily motion but not his distance: a limit of Chapter 4.
 */
export function V07Year({ card }: { card: SankrantisCard }) {
  const { dakshinayana, uttarayana } = card.ayanas;
  const { vernal, autumnal } = card.visuvats;
  return (
    <>
      <div className="table-scroll">
        <GridTable
          headers={["Sign", "Month", "Entered", "Kind", "Punyakala each side (nadis)"]}
          rows={card.sankrantis.map((e) => [
            e.sign,
            e.masa,
            fmtDate(e.date),
            e.kind === "plain" ? "" : e.kind,
            fmt(e.punyakala_each_side_nadis),
          ])}
        />
      </div>
      <KVTable
        rows={[
          ["Vernal equinox (Mesha)", fmtDate(vernal.date)],
          ["Autumnal equinox (Tula)", fmtDate(autumnal.date)],
          ["Southern progress begins (Karka)", fmtDate(dakshinayana.date)],
          ["Northern progress begins (Makara)", fmtDate(uttarayana.date)],
          ["Gap to the tropical solstice (ayanamsha)", `${fmt(dakshinayana.ayanamsha)}°`],
          ["Length of the solar year", `${fmt(card.year_days)} days`],
        ]}
      />
      <div className="table-scroll">
        <GridTable
          headers={["Season", "Begins at", "From", "To", "Days"]}
          rows={card.ritus.map((r) => [
            `${r.name} (${r.english})`,
            r.start_sign,
            fmtDate(r.start),
            fmtDate(r.end),
            fmt(r.days),
          ])}
        />
      </div>
    </>
  );
}
