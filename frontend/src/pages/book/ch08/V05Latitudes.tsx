import { fmt } from "../ch01/scale";
import type { LatitudesCard } from "./types";

/**
 * viii.5-9 — the latitudes (viksepa).
 *
 * Each junction-star's latitude is reckoned from its point of declination
 * (apakrama) and is north or south of it. The verses read these as polar
 * latitudes; the library's `star_position` treats them as ecliptic ones, which
 * matters most for Abhijit, at sixty degrees north.
 */
export function V05Latitudes({ card }: { card: LatitudesCard }) {
  return (
    <>
      <div className="table-scroll">
        <table className="ss-grid">
          <thead>
            <tr>
              <th>#</th>
              <th>Asterism</th>
              <th>Latitude</th>
            </tr>
          </thead>
          <tbody>
            {card.rows.map((r) => (
              <tr key={r.number} style={r.selected ? { fontWeight: 600 } : undefined}>
                <td>{r.number}</td>
                <td>
                  {r.name}
                  <span className="ss-note"> {r.star}</span>
                </td>
                <td>{r.latitude === 0 ? r.direction : `${fmt(Math.abs(r.latitude))}° ${r.direction}`}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
