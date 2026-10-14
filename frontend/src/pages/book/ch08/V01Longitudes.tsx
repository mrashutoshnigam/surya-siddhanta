import { KVTable } from "../../../components/Tables";
import { dms, fmt } from "../ch01/scale";
import type { LongitudesCard } from "./types";

/**
 * viii.1-4 — the polar longitudes (dhruva).
 *
 * v.1 multiplies each asterism's share by ten and adds the minutes of the
 * bhogas before it; v.2-5 print the shares. Each bhoga is 13°20′ = 800′, so
 * the n-th asterism stands at share × 10 + 800 × (n − 1) minutes. Four are
 * placed by position instead (v.4). Every figure below is derived from the
 * verse and set beside the library's catalog; the last column is that check.
 */
export function V01Longitudes({ card }: { card: LongitudesCard }) {
  return (
    <>
      <div className="table-scroll">
        <table className="ss-grid">
          <thead>
            <tr>
              <th>#</th>
              <th>Asterism</th>
              <th>Share</th>
              <th>Earlier bhogas</th>
              <th>Polar longitude</th>
              <th>Catalog</th>
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
                <td>{r.share === null ? "—" : `${r.share} × 10′`}</td>
                <td>{r.preceding_minutes === null ? <em>{r.rule}</em> : `${fmt(r.preceding_minutes)}′`}</td>
                <td>{dms(r.degrees)}</td>
                <td>{r.matches ? "✓" : `✗ ${dms(r.library_degrees)}`}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <KVTable
        rows={[
          ["Abhijit (end of Purva-Ashadha's bhoga)", `${dms(card.abhijit_degrees)} — catalog ${dms(card.abhijit_library_degrees)}`],
        ]}
      />
    </>
  );
}
