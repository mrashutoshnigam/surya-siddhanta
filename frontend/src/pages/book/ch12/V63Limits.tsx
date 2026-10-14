import { GridTable, KVTable } from "../../../components/Tables";
import { fmt } from "../ch01/scale";
import type { LimitsCard } from "./types";

/**
 * xii.63-68 — where the Sun is lost, and where he is overhead.
 *
 * The polar-day subtraction repeated with the declination reached at one and
 * two signs of longitude. Beyond those parallels the Sun is unseen for four
 * and two signs of his course. The overhead band is a fifteenth of the
 * circumference, 24 degrees: the tropics.
 */
export function V63Limits({ card }: { card: LimitsCard }) {
  return (
    <>
      <div className="table-scroll">
        <GridTable
          headers={["Sun at", "Declination", "Parallel", "Yojanas from equator", "Signs unseen beyond"]}
          rows={card.limits.map((l) => [
            `${fmt(l.sign_longitude)}°`,
            `${fmt(l.declination)}°`,
            <strong key="lat">{fmt(l.latitude)}°</strong>,
            fmt(l.yojanas_from_equator),
            l.signs_invisible,
          ])}
        />
      </div>
      <KVTable
        title="Overhead band"
        rows={[
          ["Half-width", `${fmt(card.overhead_band.degrees)}°`],
          ["In yojanas", `${fmt(card.overhead_band.yojanas)} yojanas`],
        ]}
      />
    </>
  );
}
