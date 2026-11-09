import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api";
import { DateInput, type DateValue } from "../../components/Inputs";
import { ErrorBox } from "../../components/Tables";
import { Slider } from "../../components/VerseCard";
import type { Chapter1Payload } from "../book/ch01/types";
import type { Chapter2Payload } from "../book/ch02/types";
import { downloadJson } from "./ResearchPanel";
import { DEMO_DATE, dateLabel, validDate } from "./lessonDates";
import "./learning-lab.css";
type Result = { date:DateValue; jd:number; node:number; motion:number; sun:number; moon:number; elongation:number };
const fmt=(v:number)=>`${v.toFixed(4)}°`;
const separation=(a:number,b:number)=>Math.abs(((a-b+540)%360)-180);
export function RahuLesson() {
 const [base,setBase]=useState<DateValue>(DEMO_DATE),[offset,setOffset]=useState(0);
 const [result,setResult]=useState<Result|null>(null),[error,setError]=useState<unknown>(null);
 const [loading,setLoading]=useState(true),[retry,setRetry]=useState(0),[selected,setSelected]=useState(0);
 const [answer,setAnswer]=useState(""),[revealed,setRevealed]=useState(false);
 const shifted=new Date(Date.UTC(base.year,base.month-1,base.day+offset));
 const date={year:shifted.getUTCFullYear(),month:shifted.getUTCMonth()+1,day:shifted.getUTCDate()};
 const dateOk=validDate(base)&&validDate(date),key=dateOk?dateLabel(date):"invalid";
 const current=Boolean(dateOk&&!loading&&!error&&result&&dateLabel(result.date)===key);
 useEffect(()=>{
  let cancelled=false;setLoading(true);setError(null);setAnswer("");setRevealed(false);
  if(!dateOk){setLoading(false);return;}
  const timer=window.setTimeout(()=>{
   Promise.all([api.bookChapter1(date),api.bookChapter2(date)]).then(([one,two])=>{
    if(cancelled)return;
    const a=one as Chapter1Payload,b=two as Chapter2Payload;
    const node=a.cards["i.43-44"].rows.find(r=>r.planet==="Moon");
    if(!node)throw new Error("The Moon’s ascending node is unavailable.");
    const t=b.cards["ii.66"];
    setResult({date,jd:a.jd,node:node.longitude,motion:node.daily_motion,sun:t.sun,moon:t.moon,elongation:t.elongation});setLoading(false);
   }).catch(e=>{if(!cancelled){setError(e);setLoading(false);}});
  },180);
  return()=>{cancelled=true;window.clearTimeout(timer);};
 },[key,retry]);
 const descending=result?(result.node+180)%360:0;
 const directions=result?[{label:"Ascending node · Rahu",value:result.node},{label:"Descending node",value:descending},{label:"Moon",value:result.moon}]:[];
 const ray=(degrees:number)=>({x2:200+135*Math.cos(degrees*Math.PI/180),y2:180-135*Math.sin(degrees*Math.PI/180)});
 const bookQuery=result?`?year=${result.date.year}&month=${result.date.month}&day=${result.date.day}`:"";
 return <div className="learning-lab"><header className="lab-header"><div><Link to="/learn">← All learning paths</Link><p className="lab-eyebrow">Learning lab / Rahu</p><h1>Where two planes meet.</h1><p>Rahu is the ascending lunar node: a direction where the lunar orbit crosses the ecliptic. Follow the node, then connect it to eclipse geometry.</p></div></header>
  <section className="lesson-objective"><p className="lab-eyebrow">Your goal</p><h2>Explain why eclipses need more than a phase</h2><p>Locate the two opposite nodes and distinguish longitude alignment from a prediction of an eclipse event.</p><p><strong>Try this:</strong> Move the date by 90 days. Compare the slowly regressing node with the Moon’s changing direction.</p></section>
  <section className="lab-controls" aria-label="Experiment date"><div className="lab-section-heading"><h2>Choose a moment</h2><button className="lab-secondary" onClick={()=>{setBase(DEMO_DATE);setOffset(0);setSelected(0);setRetry(v=>v+1);}}>Reset demo</button></div>
   <DateInput value={base} onChange={v=>{setBase(v);setOffset(0);}} minYear={1600} maxYear={2600} dayStep={1}/><Slider label="Move from your chosen date" value={offset} min={-90} max={90} suffix="days" onChange={setOffset}/>
   <p className="lab-caption">Whole calendar days, 1600–2600 CE · midnight in Ujjain mean time · sidereal longitude.</p>
   <div className="lab-status" role="status">{!dateOk?"Enter a valid calendar date using a whole day.":loading?`Calculating ${key}…`:error?"The calculation could not load. Check the backend, then retry.":`Showing ${result?dateLabel(result.date):key} · Ujjain mean time`}</div><ErrorBox error={error}/>{Boolean(error)&&<button className="lab-secondary" onClick={()=>setRetry(v=>v+1)}>Retry calculation</button>}
  </section>
  {result&&<>{!current&&<p className="lab-stale">Last successful result: {dateLabel(result.date)}. The diagram has not updated to the requested date.</p>}
   <section className="lab-experiment" aria-busy={loading}><div className="lab-visual"><p className="lab-eyebrow">Observe / node directions</p>
    <svg className="lesson-diagram" viewBox="0 0 400 370" role="img" aria-label={`${directions[selected].label} ${fmt(directions[selected].value)}; ascending node ${fmt(result.node)}, descending node ${fmt(descending)}, Sun ${fmt(result.sun)}, Moon ${fmt(result.moon)}`}>
     <circle cx="200" cy="180" r="135" className="lab-dial-border"/>
     <line x1={200-135*Math.cos(result.node*Math.PI/180)} y1={180+135*Math.sin(result.node*Math.PI/180)} {...ray(result.node)} className="lab-dial-guide"/>
     <line x1="200" y1="180" {...ray(result.sun)} className="lab-mean-ray"/><line x1="200" y1="180" {...ray(directions[selected].value)} className="lab-selected-ray"/>
     <circle cx="200" cy="180" r="5" className="lab-earth-point"/><text x="180" y="202">Earth</text><text x="343" y="184">0°</text><text x="80" y="350">Dashed ray: Sun · solid: selected</text>
    </svg><p className="lab-caption">Angular projection onto the ecliptic; orbital tilt is not drawn. Angles increase counterclockwise from sidereal Aries. The faint diameter joins the two nodes.</p></div>
    <div className="lab-calculation node-values"><p className="lab-eyebrow">Explain / two crossings</p><h2>Opposite directions</h2><ol className="lab-steps">{directions.map((d,i)=><li key={d.label}><button aria-pressed={selected===i} className={selected===i?"is-selected":""} onClick={()=>setSelected(i)}><span>{i+1}</span><span>{d.label}</span><strong>{fmt(d.value)}</strong></button></li>)}</ol>
     <p>Descending node = (ascending node + 180°) mod 360°.</p><p>Node mean motion: {result.motion.toFixed(6)}°/day. Its negative sign denotes regression.</p><p>Moon’s nearest-node longitude distance: {fmt(Math.min(separation(result.moon,result.node),separation(result.moon,descending)))}.</p><p>Sun–Moon elongation: {fmt(result.elongation)}.</p>
     <Link to={`/book/1${bookQuery}#i.43-44`}>Inspect the nodes · Chapter 1, 43–44 →</Link>
    </div></section>
   <section className="lesson-context"><p className="lab-eyebrow">Connect / eclipses</p><h2>Phase and orbital alignment work together</h2><p>Solar eclipses require new Moon and proximity to a node. Lunar eclipses require full Moon and proximity to a node. The tilted lunar orbit is why a new or full Moon does not produce an eclipse every month.</p><p>This lesson reports longitude geometry only. Eclipse occurrence, contacts and local visibility also depend on latitude, apparent sizes and observer geometry. Use the dedicated eclipse calculators to inspect their implemented procedures.</p><p><Link to="/eclipse/solar">Solar eclipse calculator →</Link> · <Link to="/eclipse/lunar">Lunar eclipse calculator →</Link></p><a href="https://science.nasa.gov/moon/eclipses/" target="_blank" rel="noreferrer">Background: NASA Eclipses and the Moon ↗</a></section>
   <section className="lab-question"><div><p className="lab-eyebrow">Check your understanding</p><h2>Why is there no eclipse every new Moon?</h2><p>Choose the condition that the phase alone does not establish.</p></div><div><div className="lab-answer-options">{["Phase and node alignment","Phase alone"].map(a=><button key={a} disabled={!current} aria-pressed={answer===a} onClick={()=>{setAnswer(a);setRevealed(false);}}>{a}</button>)}</div><button className="lab-primary" disabled={!current||!answer} onClick={()=>setRevealed(true)}>Check my answer</button>{revealed&&current&&<p className="lab-feedback" role="status">{answer==="Phase and node alignment"?"Correct.":"Review the geometry."} The Moon must also lie near the ecliptic at a node; phase alone does not establish that alignment.</p>}</div></section>
   <button className="lab-secondary" disabled={!current} onClick={()=>downloadJson({...result,body:"Rahu",ascending_node:result.node,descending_node:descending,time_basis:"Ujjain mean time",longitude_frame:"sidereal",source:"Existing book APIs: Chapter 1, 43–44; Chapter 2, 66",event_prediction:false},`rahu-lesson-${dateLabel(result.date)}.json`)}>Download this calculation ↓</button>
  </>}
  {!result&&<p role="status">{loading?"Preparing node geometry…":"A successful calculation will appear here."}</p>}<p><Link className="lab-next" to="/learn">Choose another learning path →</Link></p>
 </div>;
}
