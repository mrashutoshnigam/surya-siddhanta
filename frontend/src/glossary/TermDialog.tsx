import { useEffect, useMemo, useRef, useState } from "react";
import katex from "katex";
import "katex/dist/katex.min.css";
import { glossaryImageUrl } from "../api";
import type { TermIndex } from "./matchTerms";
import { CATEGORY_LABELS, Equation } from "./types";

/**
 * One equation, typeset by KaTeX.
 *
 * `trust: false` refuses \href, \url and friends, and KaTeX escapes all
 * text it emits, so its HTML is safe to inject. Bad LaTeX renders as red
 * source rather than throwing.
 */
function EquationBlock({ equation }: { equation: Equation }) {
  const html = useMemo(
    () =>
      katex.renderToString(equation.latex, {
        displayMode: true,
        throwOnError: false,
        trust: false,
        strict: "ignore",
      }),
    [equation.latex],
  );
  return (
    <figure className="term-equation">
      <div dangerouslySetInnerHTML={{ __html: html }} />
      {equation.caption && <figcaption>{equation.caption}</figcaption>}
    </figure>
  );
}

/** "SS.1.29" → "SS 1.29", the way the book pages print a verse. */
function formatCite(cite: string): string {
  return cite.replace(/^SS\./, "SS ");
}

/**
 * The popup with a term's full definition.
 *
 * A native <dialog> opened modally: the browser supplies Escape, the
 * backdrop and an inert page behind it. Related terms open in place, and
 * a Back button walks the trail. Focus returns to whatever opened it.
 */
export function TermDialog({
  id,
  index,
  onClose,
}: {
  id: string;
  index: TermIndex;
  onClose: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const [trail, setTrail] = useState<string[]>([id]);
  const [imageFailed, setImageFailed] = useState(false);

  useEffect(() => setTrail([id]), [id]);

  useEffect(() => {
    const dialog = ref.current;
    const opener = document.activeElement as HTMLElement | null;
    if (dialog && !dialog.open) dialog.showModal();
    // No dialog.close() here: its "close" event fires asynchronously, and
    // under StrictMode's mount-unmount-mount it would land after the
    // re-open and dismiss the popup. Unmounting removes it from the top
    // layer anyway.
    return () => opener?.focus();
  }, []);

  const currentId = trail[trail.length - 1];
  const term = index.terms.get(currentId);
  // A new term starts at its top, with its image given a fresh chance.
  useEffect(() => {
    setImageFailed(false);
    if (ref.current) ref.current.scrollTop = 0;
  }, [currentId]);

  const related = (term?.related ?? []).flatMap((rid) => index.terms.get(rid) ?? []);

  return (
    <dialog
      ref={ref}
      className="term-dialog"
      aria-labelledby="term-dialog-title"
      onClose={onClose}
      onClick={(e) => {
        // A click on the dialog element itself (not its content) is a
        // click on the backdrop.
        if (e.target === e.currentTarget) e.currentTarget.close();
      }}
    >
      <div className="term-dialog-inner">
        <header className="term-dialog-head">
          {trail.length > 1 && (
            <button
              type="button"
              className="term-dialog-back"
              onClick={() => setTrail((t) => t.slice(0, -1))}
            >
              ← Back
            </button>
          )}
          <button
            type="button"
            className="term-dialog-close"
            aria-label="Close"
            onClick={() => ref.current?.close()}
          >
            ×
          </button>
        </header>

        {!term ? (
          <p className="glossary-note">This term is not in the glossary.</p>
        ) : (
          <>
            <span className="term-category">{CATEGORY_LABELS[term.category]}</span>
            <h2 id="term-dialog-title">{term.term}</h2>
            {term.aliases && term.aliases.length > 0 && (
              <p className="term-aliases">Also written: {term.aliases.join(", ")}</p>
            )}
            <p className="term-short">{term.short}</p>
            {term.full.map((paragraph, i) => (
              <p key={i} className="term-full">
                {paragraph}
              </p>
            ))}

            {term.equations?.map((eq, i) => <EquationBlock key={i} equation={eq} />)}

            {term.image && !imageFailed && (
              <figure className="term-image">
                <img
                  src={glossaryImageUrl(term.image.src)}
                  alt={term.image.alt}
                  loading="lazy"
                  onError={() => setImageFailed(true)}
                />
              </figure>
            )}

            {term.cite && term.cite.length > 0 && (
              <p className="term-cite">
                <span>Verses:</span> {term.cite.map(formatCite).join(" · ")}
              </p>
            )}

            {related.length > 0 && (
              <div className="term-related">
                <span>See also</span>
                <div>
                  {related.map((r) => (
                    <button
                      key={r.id}
                      type="button"
                      className="term-chip"
                      onClick={() => setTrail((t) => [...t, r.id])}
                    >
                      {r.term}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </dialog>
  );
}
