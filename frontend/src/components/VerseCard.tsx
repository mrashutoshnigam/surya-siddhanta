import type { ReactNode } from "react";

/**
 * The chrome around one verse's panel: the verse number and title, the
 * one-line statement of what the verse computes, the verse text with its
 * corpus citation, and a slot for whatever inputs and outputs the verse
 * itself calls for.
 *
 * Verse text is optional on purpose. The corpus lives outside this
 * repository and need not be reachable; when it is not, the card still
 * computes and says only that the text is missing.
 */
export function VerseCard({
  id,
  prefix = "i",
  verses,
  title,
  does,
  dateDependent,
  text,
  citations,
  children,
}: {
  id: string;
  prefix?: string;
  verses: string;
  title: string;
  does: string;
  dateDependent: boolean;
  text: string | null;
  citations: string[];
  children: ReactNode;
}) {
  return (
    <section className="verse-card" id={id}>
      <header className="verse-card-head">
        <div>
          <span className="verse-ref">{prefix}.{verses}</span>
          <h2>{title}</h2>
        </div>
        <span className={"verse-tag" + (dateDependent ? " live" : "")}>
          {dateDependent ? "varies with the date" : "fixed"}
        </span>
      </header>

      <p className="verse-does">{does}</p>

      {text ? (
        <blockquote className="verse-text">
          {text}
          <cite>{citations.join(", ")}</cite>
        </blockquote>
      ) : (
        <p className="verse-text-missing">
          Verse text unavailable — the corpus is not reachable, or these
          verses are among its gaps.
        </p>
      )}

      <div className="verse-panel">{children}</div>
    </section>
  );
}

/**
 * A labelled slider with its own numeric readout, the control every
 * interactive card is built from.
 */
export function Slider({
  label,
  value,
  min,
  max,
  step = 1,
  suffix,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step?: number;
  suffix?: string;
  onChange: (v: number) => void;
}) {
  return (
    <label className="slider">
      <span className="slider-label">
        {label}
        <strong>
          {value.toLocaleString("en-US", { maximumFractionDigits: 4 })}
          {suffix ? ` ${suffix}` : ""}
        </strong>
      </span>
      <input
        type="range"
        value={value}
        min={min}
        max={max}
        step={step}
        onChange={(e) => onChange(Number(e.target.value))}
      />
    </label>
  );
}

/** A row of mutually exclusive choices — a unit, a planet, a chain. */
export function Picker<T extends string>({
  label,
  value,
  options,
  onChange,
}: {
  label?: string;
  value: T;
  options: { value: T; label: string }[];
  onChange: (v: T) => void;
}) {
  return (
    <div className="picker">
      {label && <span className="picker-label">{label}</span>}
      <div className="chip-row">
        {options.map((option) => (
          <button
            key={option.value}
            type="button"
            className={"chip chip-button" + (option.value === value ? " selected" : "")}
            onClick={() => onChange(option.value)}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  );
}
