import type { ReactNode } from "react";

export function KVTable({ title, rows }: { title?: string; rows: [string, ReactNode][] }) {
  return (
    <div className="ss-block">
      {title && <h3>{title}</h3>}
      <table className="ss-table">
        <tbody>
          {rows.map(([k, v], i) => (
            <tr key={i}>
              <th>{k}</th>
              <td>{v}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function GridTable({ headers, rows }: { headers: string[]; rows: ReactNode[][] }) {
  return (
    <table className="ss-grid">
      <thead>
        <tr>
          {headers.map((h, i) => (
            // Keyed on position, not text: a table may repeat a header
            // (the hora grid runs Hora/Lord four times across).
            <th key={i}>{h}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((r, i) => (
          <tr key={i}>
            {r.map((c, j) => (
              <td key={j}>{c}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export function ErrorBox({ error }: { error: unknown }) {
  if (!error) return null;
  const message = error instanceof Error ? error.message : String(error);
  return <div className="ss-error">Error: {message}</div>;
}

export function PageHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="page-header">
      <h1>{title}</h1>
      {subtitle && <p className="subtitle">{subtitle}</p>}
    </div>
  );
}
