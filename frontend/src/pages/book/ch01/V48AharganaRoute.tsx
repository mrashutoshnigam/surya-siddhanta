import { useEffect, useState } from "react";
import { api } from "../../../api";
import { KVTable } from "../../../components/Tables";
import { Slider } from "../../../components/VerseCard";
import { grouped } from "./scale";
import type { AharganaRoute, AharganaRouteCard } from "./types";

/**
 * i.48-51 — the ahargana by the text's own route.
 *
 * The one card whose sliders do not compute in the browser. Its chain runs
 * through 7 × 10¹¹ lunar days, and the adhimasa proportion multiplies that
 * by 1.6 million, which leaves the exact integers a double can hold. So
 * the three sliders post to /calc/ahargana-verse — the same route the
 * chapter page's own payload used — debounced, and the card shows the
 * server's answer.
 *
 * The sliders start at the mean luni-solar triple for the page's date. The
 * difference row is the honest part: the triple is derived from mean
 * places, so near a month boundary it can land a month out, and the card
 * says by how much rather than hiding it.
 */
export function V48AharganaRoute({ card }: { card: AharganaRouteCard }) {
  const [years, setYears] = useState(card.input.years);
  const [months, setMonths] = useState(card.input.months);
  const [tithis, setTithis] = useState(card.input.tithis);
  const [route, setRoute] = useState<AharganaRoute>(card.route);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const timer = window.setTimeout(() => {
      api
        .aharganaVerse({ years, months, tithis, from_creation: false })
        .then((result) => {
          if (!cancelled) {
            setRoute(result as AharganaRoute);
            setError(null);
          }
        })
        .catch((err: unknown) => {
          if (!cancelled) setError(err instanceof Error ? err.message : String(err));
        });
    }, 120);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [years, months, tithis]);

  const difference = route.civil_days - card.direct_ahargana;

  return (
    <>
      <Slider
        label="Years elapsed"
        value={years}
        min={0}
        max={6000}
        step={1}
        suffix="years"
        onChange={setYears}
      />
      <Slider
        label="Luni-solar months of the current year"
        value={months}
        min={0}
        max={12}
        step={1}
        onChange={setMonths}
      />
      <Slider
        label="Tithis of the current month"
        value={tithis}
        min={0}
        max={29}
        step={1}
        onChange={setTithis}
      />

      <KVTable
        title="The chain of v.48-51"
        rows={[
          ["elapsed", `${grouped(years)} y., ${months} m., ${tithis} d.`],
          ["solar months", grouped(route.solar_months)],
          ["+ intercalary (adhimasa)", grouped(route.adhimasa)],
          ["= lunar months", grouped(route.lunar_months)],
          ["× 30 = lunar days", grouped(route.lunar_days)],
          ["− omitted (tithikshaya)", grouped(route.tithikshaya)],
          ["= civil days, from creation", grouped(route.creation_to_kali_civil_days + route.civil_days)],
          ["− creation to the Kali epoch", grouped(route.creation_to_kali_civil_days)],
          ["= ahargana", <strong>{grouped(route.civil_days)}</strong>],
          ["by subtraction from the epoch", grouped(card.direct_ahargana)],
          [
            "difference",
            difference === 0 ? "none — the two routes agree" : `${grouped(difference)} days`,
          ],
        ]}
      />

      <KVTable
        title="The proportions the route runs on"
        rows={[
          ["Solar months in an Age", grouped(card.solar_months_per_mahayuga)],
          ["Intercalary months in an Age", grouped(card.adhimasa_per_mahayuga)],
          ["Lunar days in an Age", grouped(card.lunar_days_per_mahayuga)],
          ["Omitted lunar days in an Age", grouped(card.tithikshaya_per_mahayuga)],
        ]}
      />

      {error && <p className="verse-note verse-note-error">Could not reach the server: {error}</p>}
      <p className="verse-note">{card.note}</p>
    </>
  );
}
