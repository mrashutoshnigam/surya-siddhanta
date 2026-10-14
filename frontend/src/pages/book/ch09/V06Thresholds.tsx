import type { ReactNode } from "react";
import { GridTable, KVTable } from "../../../components/Tables";
import { fmt } from "../ch01/scale";
import type { ThresholdsCard } from "./types";

/**
 * ix.6-9 — the limits of visibility.
 *
 * The verses give each planet's distance from the Sun, in degrees of time,
 * inside which it cannot be seen. Venus and Mercury have two limits, by
 * whether they are retrograding. The library applies them to the ecliptic
 * elongation, not to oblique ascension, so the figures here are an
 * approximation of the verse's own.
 */
export function V06Thresholds({ card }: { card: ThresholdsCard }) {
  return (
    <>
      <GridTable
        headers={["Planet", "Retrograde", "Direct"]}
        rows={card.rows.map((r) => {
          const bold = (v: ReactNode) => (r.selected ? <strong>{v}</strong> : v);
          return [bold(r.planet), bold(`${r.retrograde}°`), bold(`${r.direct}°`)];
        })}
      />
      <KVTable
        rows={[
          [`${card.planet}, elongation from the Sun`, `${fmt(card.elongation)}°`],
          ["Limit that applies", `${card.threshold}° (${card.retrograde ? "retrograde" : "direct"})`],
          ["Margin", `${fmt(card.margin)}°`],
          ["The planet is", <strong>{card.visible ? "visible" : "lost in the Sun's rays"}</strong>],
        ]}
      />
      <p className="ss-note">
        The verses measure these distances in oblique ascension (degrees of time); the library
        uses the plain ecliptic elongation.
      </p>
    </>
  );
}
