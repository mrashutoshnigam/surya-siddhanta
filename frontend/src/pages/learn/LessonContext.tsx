import { Link } from "react-router-dom";
import type { Chapter2Payload } from "../book/ch02/types";
import type { LessonBody } from "./lessons";
export function LessonContext({body,payload,bookQuery}:{body:LessonBody;payload:Chapter2Payload;bookQuery:string}) {
 if(["Mercury","Venus","Jupiter","Saturn"].includes(body)) {
  const inner=body === "Mercury" || body === "Venus";
  const pair=inner ? ["Mercury","Venus"] : ["Jupiter","Saturn"];
  const rows=pair.map(name=>payload.cards["ii.43-45"].rows.find(r=>r.body===name)!);
  const sun=payload.cards["ii.66"].sun;
  const separation=(longitude:number)=>Math.abs(((longitude-sun+540)%360)-180);
  return <section className="lesson-context"><p className="lab-eyebrow">Compare / {inner ? "inner" : "outer"} planets</p><h2>{pair.join(" and ")} on the same date</h2>
   <p>Both use the five-position correction sequence. Read each row across to compare the two calculations; every value comes from the same API response and date.</p>
   <div className="lesson-table-wrap"><table className="lesson-table"><caption>Sidereal longitudes in degrees</caption><thead><tr><th scope="col">Stage</th>{pair.map(name=><th scope="col" key={name}>{name}</th>)}</tr></thead><tbody>{rows[0].stages.map((stage,i)=><tr key={stage.label}><th scope="row">{stage.label}</th>{rows.map(r=><td key={r.body}>{r.stages[i].longitude.toFixed(4)}°</td>)}</tr>)}<tr><th scope="row">Separation from Sun</th>{rows.map(r=><td key={r.body}>{separation(r.true_longitude).toFixed(4)}°</td>)}</tr></tbody></table></div>
   <p className="lab-caption">Sun separation is the shortest longitude difference (0–180°), not a three-dimensional angular distance or a visibility prediction. {inner ? "Mercury and Venus have their own sighrocca rules in the implementation; their mean-place conventions should not be read as modern heliocentric orbits." : "The uniform mean directions change more slowly than for the Sun. Corrections can change the apparent motion; this single-date table does not identify retrograde intervals."}</p>
   <Link to={`/learn/${pair.find(name=>name!==body)!.toLowerCase()}${bookQuery}`}>Explore {pair.find(name=>name!==body)} →</Link><p><Link to={`/book/2${bookQuery}#ii.43-45`}>Inspect both calculations in Chapter 2 →</Link></p>
  </section>;
 }
 if(body === "Moon") {
  const t=payload.cards["ii.66"];
  const angle=t.elongation*Math.PI/180;
  return <section className="lesson-context"><p className="lab-eyebrow">Connect / lunar calendar</p><h2>From separation to tithi</h2>
   <p>A tithi divides the full 360° Sun–Moon longitude cycle into thirty 12° intervals. It is an angular interval, so it need not last one civil day.</p>
   <div className="lesson-two-column"><svg viewBox="0 0 400 330" className="lesson-diagram" role="img" aria-label={`Moon elongation ${t.elongation.toFixed(4)} degrees counterclockwise from the Sun direction`}>
    <circle cx="180" cy="165" r="115" className="lab-dial-border"/><line x1="180" y1="165" x2="295" y2="165" className="lab-mean-ray"/>
    <line x1="180" y1="165" x2={180+115*Math.cos(angle)} y2={165-115*Math.sin(angle)} className="lab-selected-ray"/>
    <circle cx={180+115*Math.cos(angle)} cy={165-115*Math.sin(angle)} r="9" className="lab-selected-point"/>
    <text x="305" y="169">Sun</text><text x="160" y="187">Earth</text><text x="70" y="315">Solid ray: Moon · dashed ray: Sun</text>
   </svg><dl className="lesson-measures"><div><dt>Elongation</dt><dd>{t.elongation.toFixed(4)}°</dd></div><div><dt>Calendar interval</dt><dd>Tithi {t.number}</dd></div><div><dt>Name</dt><dd>{t.name}</dd></div><div><dt>Paksha</dt><dd>{t.paksha === "shukla" ? "Waxing" : "Waning"}</dd></div></dl></div>
   <p>Elongation = (Moon − Sun) wrapped to 0–360°. Tithi = floor(elongation ÷ 12°) + 1. Progress through this tithi: {(t.fraction*100).toFixed(1)}%.</p>
   <p className="lab-caption">The drawing places the Sun direction at 0° for comparison; it is not the absolute sidereal dial above or an image of the illuminated lunar disc. New, quarter and full phases correspond approximately to separations 0°, 90°, 180° and 270°.</p>
   <Link to={`/book/2${bookQuery}#ii.66`}>Inspect tithi · Chapter 2, 66 →</Link><p><a href="https://science.nasa.gov/moon/moon-phases/" target="_blank" rel="noreferrer">Background: NASA Moon phases ↗</a></p>
  </section>;
 }
 if(body !== "Sun") return null;
 const d=payload.cards["ii.60-63"];
 return <section className="lesson-context"><p className="lab-eyebrow">Connect / seasons</p><h2>Why does day length change?</h2><p>The position diagram above uses sidereal longitude. For the seasonal calculation the API converts the Sun to tropical longitude, measured from the moving equinox.</p>
  <dl className="lesson-measures"><div><dt>Tropical Sun</dt><dd>{d.sun_tropical.toFixed(4)}°</dd></div><div><dt>Declination</dt><dd>{d.declination.toFixed(4)}°</dd></div><div><dt>Day</dt><dd>{d.day_ghatis.toFixed(3)} ghatis</dd></div><div><dt>Night</dt><dd>{d.night_ghatis.toFixed(3)} ghatis</dd></div></dl>
  <div className="lesson-day-bar" role="img" aria-label={`Day ${d.day_ghatis.toFixed(3)} ghatis, night ${d.night_ghatis.toFixed(3)} ghatis`}><span style={{width:`${d.day_ghatis/60*100}%`}}>Day</span><span>Night</span></div>
  <p className="lab-caption">Latitude {d.latitude}° · Ujjain · 60 ghatis = 24 hours. Day length uses the library’s hour-angle formula; it is not a direct rendering of the text’s tabular rule.</p><Link to={`/book/2${bookQuery}#ii.60-63`}>Inspect day length · Chapter 2, 60–63 →</Link>
 </section>;
}
