import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { bookDateFromSearch } from "../book/dates";
import { api } from "../../api";
import { DateInput, type DateValue } from "../../components/Inputs";
import { ErrorBox } from "../../components/Tables";
import { Slider } from "../../components/VerseCard";
import type { Chapter2Payload, TruePlaceCard, VerseRecord } from "../book/ch02/types";
import { LongitudeDial } from "./LongitudeDial";
import { downloadJson, ResearchPanel } from "./ResearchPanel";
import "./learning-lab.css";
import { LessonContext } from "./LessonContext";
import { LESSONS, type LessonBody } from "./lessons";

type PlanetRow = TruePlaceCard["rows"][number];
import { DEMO_DATE, dateLabel, validDate } from "./lessonDates";
const EXPLANATIONS = [
  "Start with uniform mean motion: where Mars would be before the corrections are applied.",
  "Apply half the first sighra correction. This gives an intermediate direction for the next calculation.",
  "Apply half the first manda correction to that intermediate direction.",
  "Return to the ORIGINAL mean longitude and add the whole manda correction. This step does not simply add to the previous row.",
  "Apply the whole sighra correction to the manda-corrected position. This is the model’s final true longitude.",
];
const REFS = ["Ch. 1, vv. 29–34, 53", "Ch. 2, vv. 43–45", "Ch. 2, vv. 43–45", "Ch. 2, vv. 43–45", "Ch. 2, vv. 43–45"];
const fmt = (v: number) => `${v.toFixed(4)}°`;
export function LearningLab({ body = "Mars" }: { body?: LessonBody }) {
  const lesson = LESSONS.find(l => l.body === body)!;
  const simple = body === "Sun" || body === "Moon";
  const location = useLocation();
  const [base, setBase] = useState<DateValue>(() => {
    const date = bookDateFromSearch(location.search, DEMO_DATE);
    return validDate(date) ? date : DEMO_DATE;
  });
  const [offset, setOffset] = useState(0);
  const [step, setStep] = useState(0);
  const [result, setResult] = useState<{ row: PlanetRow; date: DateValue; jd: number; payload: Chapter2Payload } | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(true);
  const [retry, setRetry] = useState(0);
  const [prediction, setPrediction] = useState<string | null>(null);
  const [revealed, setRevealed] = useState(false);
  const [verses, setVerses] = useState<VerseRecord[]>([]);
  const [verseState, setVerseState] = useState("Loading source text…");
  const baseOk = validDate(base);
  const shifted = new Date(Date.UTC(base.year, base.month - 1, base.day + offset));
  const requested = { year: shifted.getUTCFullYear(), month: shifted.getUTCMonth() + 1, day: shifted.getUTCDate() };
  const dateOk = baseOk && validDate(requested);
  const requestKey = dateOk ? dateLabel(requested) : "invalid";
  const current = Boolean(dateOk && !loading && !error && result && dateLabel(result.date) === requestKey);

  useEffect(() => {
    let cancelled = false;
    setPrediction(null); setRevealed(false); setLoading(true); setError(null);
    if (!dateOk) { setLoading(false); return; }
    const timer = window.setTimeout(() => {
      api.bookChapter2(requested).then(raw => {
        if (cancelled) return;
        const payload = raw as Chapter2Payload;
        const row = payload.cards["ii.43-45"].rows.find(r => r.body === body);
        if (!row || row.stages.length !== (simple ? 2 : 5)) throw new Error(`The ${body} calculation stages are unavailable.`);
        setResult({ row, date: requested, jd: payload.jd, payload }); setLoading(false);
      }).catch(e => { if (!cancelled) { setError(e); setLoading(false); } });
    }, 180);
    return () => { cancelled = true; window.clearTimeout(timer); };
  }, [requestKey, retry, body]);

  useEffect(() => {
    let cancelled = false;
    api.corpusVerses(2).then(raw => {
      if (cancelled) return;
      const records = (raw as { verses: VerseRecord[] }).verses ?? [];
      const found = records.filter(v => v.verse >= (simple ? 39 : 43) && v.verse <= (simple ? 39 : 45) && v.translation_en?.trim());
      setVerses(found);
      setVerseState(found.length === (simple ? 1 : 3) ? "" : "Some verse text is unavailable in the connected corpus. The calculation and chapter references remain available.");
    }).catch(() => { if (!cancelled) setVerseState("Source text is unavailable. Open Chapter 2 for the calculation references; this lesson still works without the corpus."); });
    return () => { cancelled = true; };
  }, [body]);

  const row = result?.row;
  const selected = row?.stages[step];
  const difference = row ? ((row.true_longitude - row.stages[0].longitude + 540) % 360) - 180 : 0;
  const answer = Math.abs(difference) < 0.00005 ? "same" : difference > 0 ? "ahead" : "behind";
  const bookQuery = result ? `?year=${result.date.year}&month=${result.date.month}&day=${result.date.day}` : "";
  function reset() { setBase(DEMO_DATE); setOffset(0); setStep(0); setPrediction(null); setRevealed(false); setRetry(v => v + 1); }

  return <div className="learning-lab">
    <header className="lab-header">
      <div><Link to="/learn">← All learning paths</Link><p className="lab-eyebrow">Learning lab / {body}</p><h1>From verse<br />to a planet’s position.</h1>
        <p>Move through time. Follow the corrections. See how an ancient model becomes a number you can inspect.</p></div>
      <div className="lab-header-note"><span>{lesson.script}</span><strong>{body}</strong><small>A guided experiment<br />in Chapters 1 &amp; 2</small></div>
    </header>

    <section className="lesson-objective"><p className="lab-eyebrow">Your goal</p><h2>{lesson.title}</h2><p>{lesson.goal}</p><p><strong>Try this:</strong> {lesson.activity}</p></section>

    <section className="lab-controls" aria-label="Experiment date">
      <div className="lab-section-heading"><div><p className="lab-eyebrow">Explore</p><h2>Choose a moment</h2></div><button type="button" className="lab-secondary" onClick={reset}>Reset demo</button></div>
      <DateInput value={base} onChange={value => { setBase(value); setOffset(0); }} minYear={1600} maxYear={2600} dayStep={1} />
      <p className="lab-caption">Use a whole calendar day, 1600–2600 CE. Dates are evaluated at midnight in Ujjain mean time, matching the book calculations.</p>
      <Slider label="Move from your chosen date" value={offset} min={-90} max={90} suffix="days" onChange={setOffset} />
      <div className="lab-status" role="status">
        {!dateOk ? "Enter a valid calendar date using a whole day." : loading ? `Calculating ${requestKey}…` : error ? "The calculation could not load. Check that the backend is running, then retry." : `Showing ${result ? dateLabel(result.date) : requestKey} · Ujjain mean time`}
      </div>
      <ErrorBox error={error} />
      {Boolean(error) && <button type="button" className="lab-secondary" onClick={() => setRetry(v => v + 1)}>Retry calculation</button>}
    </section>

    {row && selected ? <>
      {!current && <p className="lab-stale">The diagram below is the last successful result for {dateLabel(result!.date)}. It has not updated to the requested date.</p>}
      <section className="lab-experiment" aria-label={`${body} calculation`} aria-busy={loading}>
        <div className="lab-visual">
          <div className="lab-section-heading"><p className="lab-eyebrow">Observe · sidereal longitude</p><span className="lab-tag">Angular view</span></div>
          <LongitudeDial mean={row.stages[0].longitude} selected={selected.longitude} label={selected.label} />
          <div className="lab-dial-legend"><span><i className="lab-legend-dashed" />Mean direction</span><span><i className="lab-legend-solid" />Selected step</span></div>
          <p className="lab-caption">0° is the start of sidereal Aries. Angles increase counterclockwise. This shows directions from Earth, not physical orbit sizes.</p>
        </div>
        <div className="lab-calculation">
          <p className="lab-eyebrow">Explain · {simple ? "two" : "five"} positions</p><h2>Follow the correction</h2>
          <p>Select a step to move the solid ray.</p>
          <ol className="lab-steps">
            {row.stages.map((stage, i) => <li key={stage.label}>
              <button type="button" aria-pressed={step === i} className={step === i ? "is-selected" : ""} onClick={() => setStep(i)}>
                <span className="lab-step-number">{i + 1}</span><span>{stage.label}{!simple && i === 3 && <small>Applied to the original mean</small>}</span><strong>{fmt(stage.longitude)}</strong>
              </button>
            </li>)}
          </ol>
          <div className="lab-explanation" aria-live="polite"><span>{simple && step > 0 ? "Ch. 2, v. 39" : REFS[step]}</span><p>{simple ? (step === 0 ? `Start with the uniform mean motion of the ${body}.` : `Apply the whole manda correction to the mean. The ${body} has no sighra stage in this pipeline.`) : EXPLANATIONS[step].replace("Mars", body)}</p>
            {selected.correction !== null && <p className="lab-equation">Correction: {selected.correction >= 0 ? "+" : "−"}{fmt(Math.abs(selected.correction))}</p>}
          </div>
          <Link to={step === 0 ? `/book/1${bookQuery}#i.52-54` : `/book/2${bookQuery}#${simple ? "ii.39" : "ii.43-45"}`}>Inspect the calculation in the book →</Link>
        </div>
      </section>

      {current && <LessonContext body={body} payload={result!.payload} bookQuery={bookQuery} />}

      <section className="lab-question" aria-labelledby="lab-question-title">
        <div><p className="lab-eyebrow">Check your understanding</p><h2 id="lab-question-title">What do the corrections change?</h2><p>Along the shortest angular separation, is the final position ahead of or behind the mean? Choose an answer, then check it.</p></div>
        <div>
          <div className="lab-answer-options" role="group" aria-label="Your prediction">
            {[['ahead', 'Ahead'], ['behind', 'Behind'], ['same', 'The same']].map(([value, label]) => <button type="button" key={value} disabled={!current} aria-pressed={prediction === value} onClick={() => { setPrediction(value); setRevealed(false); }}>{label}</button>)}
          </div>
          <button type="button" className="lab-primary" disabled={!prediction || !current} onClick={() => { setRevealed(true); setStep(row.stages.length - 1); }}>Check my answer</button>
          {revealed && current && <p className="lab-feedback" role="status">{prediction === answer ? "Correct." : "Look at the two directions again."} The final longitude is {Math.abs(difference).toFixed(4)}° {answer === "same" ? "from the mean (the same to four decimals)" : `${answer === "ahead" ? "ahead of" : "behind"} the mean`}. “True” here means corrected within the SS model; it does not imply agreement with modern observations.</p>}
        </div>
      </section>

      <details className="lab-details"><summary>Read the source verses · Chapter 2, {simple ? "39" : "43–45"}</summary>
        {verseState && <p>{verseState}</p>}
        {verses.map(v => <blockquote key={v.id}><p>{v.translation_en}</p><cite>{v.id} · connected corpus translation</cite></blockquote>)}
        <Link to={`/book/2${bookQuery}#${simple ? "ii.39" : "ii.43-45"}`}>Open Chapter 2 →</Link>
      </details>
      <button type="button" className="lab-secondary lab-export" disabled={!current} onClick={() => downloadJson({ date: result!.date, jd: result!.jd, time_basis: "Ujjain mean time", longitude_frame: "sidereal", lesson_context: body === "Sun" ? result!.payload.cards["ii.60-63"] : body === "Moon" ? result!.payload.cards["ii.66"] : { sun_longitude: result!.payload.cards["ii.66"].sun, separation_definition: "absolute shortest longitude difference in degrees", comparison_rows: result!.payload.cards["ii.43-45"].rows.filter(r => (body === "Mercury" || body === "Venus" ? ["Mercury", "Venus"] : body === "Jupiter" || body === "Saturn" ? ["Jupiter", "Saturn"] : ["Mars"]).includes(r.body)) }, source: `SS Chapter 2, ${simple ? "verse 39" : "verses 43–45"}; existing book API`, ...row }, `${body.toLowerCase()}-lesson-${dateLabel(result!.date)}.json`)}>Download this calculation ↓</button>
    </> : <div className="lab-empty">{loading ? "Preparing the longitude diagram and correction steps…" : body === "Mars" ? "A successful calculation will appear here. The saved research panel below remains available." : "A successful calculation will appear here. Check the date and backend, then retry."}</div>}

    {body === "Mars" && <ResearchPanel />}
    <Link className="lab-next" to="/learn">Choose the next learning path →</Link>
    <footer className="lab-endnote">One historical model, an inspectable calculation, and a modern reference. Use each for the question it can answer.</footer>
  </div>;
}
