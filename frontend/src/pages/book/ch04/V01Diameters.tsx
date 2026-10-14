import { KVTable } from "../../../components/Tables";
import { fmt } from "../ch01/scale";
import type { DiametersCard } from "./types";

/** iv.1-2 — the diameters of the Sun and Moon, true and apparent. */
export function V01Diameters({ card }: { card: DiametersCard }) {
  return (
    <KVTable
      rows={[
        ["True diameters", `Sun ${fmt(card.sun_yojana)} · Moon ${fmt(card.moon_yojana)} yojanas`],
        ["Yojanas to a minute", fmt(card.yojana_per_arcmin)],
        ["Sun, apparent", `${fmt(card.sun_arcmin)}′ (mean ${fmt(card.sun_mean_arcmin)}′)`],
        ["Moon, mean", `${fmt(card.moon_mean_arcmin)}′`],
        ["Moon, at her distance now", <strong>{fmt(card.moon_arcmin)}′</strong>],
        ["Moon now ÷ mean", fmt(card.moon_ratio)],
      ]}
    />
  );
}
