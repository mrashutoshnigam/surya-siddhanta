import { GridTable, KVTable } from "../../../components/Tables";
import { fmt } from "../ch01/scale";
import type { ConverterCard } from "./types";

const years = (n: number) => n.toLocaleString();

/**
 * xiv.18-21 — civil time, and the times of the gods, Prajapati and Brahma.
 *
 * Every mode's unit is a length in civil days, so converting is a ratio; the
 * table shows the lengths so the arithmetic can be checked. Fourteen
 * manvantaras of 71 mahayugas and fifteen sandhis of one krita yuga make a
 * kalpa exactly.
 */
export function V18Converter({ card }: { card: ConverterCard }) {
  const s = card.structure;
  return (
    <>
      <KVTable
        rows={[
          [
            `${fmt(card.value)} ${card.from_mana}`,
            <strong key="r">
              {fmt(card.result)} {card.to_mana}
            </strong>,
          ],
        ]}
      />
      <div className="table-scroll">
        <GridTable
          headers={["Mode", "Unit", "Length in civil days"]}
          rows={card.units.map((u) => [u.iast, u.unit, fmt(u.unit_days)])}
        />
      </div>
      <KVTable
        title="A kalpa"
        rows={[
          [`${s.manvantaras} manvantaras × ${years(s.manvantara_years)} years`, years(s.manvantaras * s.manvantara_years)],
          [`${s.sandhis} sandhis × ${years(s.sandhi_years)} years`, years(s.sandhis * s.sandhi_years)],
          ["Total", <strong key="t">{years(s.total_years)} years</strong>],
        ]}
      />
    </>
  );
}
