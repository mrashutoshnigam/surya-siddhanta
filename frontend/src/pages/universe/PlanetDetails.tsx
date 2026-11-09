import { Link } from "react-router-dom";
import { modelLabel } from "./math";
import type { BodyInfo, Model, Snapshot } from "./types";
import { iso } from './math';

const number=(value:number,digits=2)=>value.toLocaleString(undefined,{maximumFractionDigits:digits});
export function PlanetDetails({body,snapshot,model,sceneTime,onAsk}: {body:BodyInfo;snapshot:Snapshot|null;model:Model;sceneTime:number;onAsk:()=>void}) {
  const row=snapshot?.model===model?snapshot.bodies[body.id]:undefined;
  const centre=model==='historical'?'Earth':'the Sun';
  const origin=body.id===(model==='historical'?'Earth':'Sun');
  const backward=model==='historical'&&(row?.motion_deg_per_day??0)<0;
  const motion=body.kind==='node'?'This marker shows where the Moon’s path crosses the ecliptic, the reference plane used for these directions. It is not a physical globe.':origin?`${body.id} stays at the centre of this view. The turning surface is a modern teaching illustration.`:body.id==='Moon'?`Follow the Moon’s changing direction from Earth${model==='modern'?' while Earth travels around the Sun':''}.`:`${model==='historical'?'Its calculated direction changes as seen from Earth':'Its position changes around the Sun'}. Surface spin and this journey are separate motions.`;
  const watch=body.kind==='node'?'Turn on motion guides and follow the Moon near the two crossing directions.':body.id==='Mars'&&model==='historical'?'Use the Mars tour to see its longitude increase, decrease, and increase again. Backward motion describes a direction seen from Earth.':body.id==='Moon'?'Watch Earth and Moon together. Speed up time to follow a month of changing directions.':origin?'Select another world to follow its journey, or switch models to change the centre.':`Select ${body.id}, enable motion guides, and compare its turning surface with its changing position relative to ${centre}.`;
  return <div className="universe-details" data-testid="planet-facts">
    <div className="universe-body-heading"><span className="universe-body-swatch" style={{background:body.color}}/>
      <div><p className="universe-eyebrow">{body.kind==="node"?"Lunar node":body.kind==="star"?"Our star":body.kind==="moon"?"Earth’s companion":"Meet a world"}</p><h2>{body.id}</h2>{body.sanskrit&&<p className="universe-sanskrit">{body.sanskrit}</p>}</div>
    </div>
    <h3>What is it?</h3><p className="universe-introduction">{body.introduction}</p>
    <section className="universe-beginner"><h3>What is moving?</h3><p>{motion}</p>{model==='historical'&&body.id!=='Earth'&&row&&<p className="universe-motion-reading"><strong>{backward?'Backward in longitude':'Forward in longitude'}</strong>{backward?' · Retrograde':' · Forward'} at the exact evaluation below.</p>}<h3>What should I watch?</h3><p>{watch}</p></section>
    {model==="historical"&&body.historical&&<section className="universe-historical-note"><h3>In Surya Siddhanta</h3><p>{body.historical}</p><Link to={body.id==="Earth"?"/book/12":body.kind==="node"?"/learn/rahu":`/learn/${body.id.toLowerCase()}`}>Explore the historical calculation <span aria-hidden="true">↗</span></Link></section>}
    <section className="universe-calculated"><h3>Calculated position</h3>
      <p className="universe-fact-caption" data-testid="snapshot-model">{modelLabel(model)} · {model==="historical"?"Earth-centered":"Sun-centered"}</p>
      {row&&snapshot?<>
        <p className="universe-exact-time">Scene time: {iso(sceneTime).slice(0,19).replace('T',' · ')} UTC</p>
        <p className="universe-exact-time" data-testid="snapshot-date">Exact at {snapshot.instant.replace("T"," · ").replace(/\.\d+Z$/,"Z")} (UTC)</p>
        <p className="universe-fact-caption">The moving scene uses interpolation. Numbers below belong to the exact time above.</p>
        <details className="universe-provenance"><summary>Numerical position</summary>
        <dl className="universe-values">
          {body.id===(model==="historical"?"Earth":"Sun")?<div><dt>Position</dt><dd>Frame origin</dd></div>:<>
            <div><dt>{model==="historical"?"Sidereal longitude":"J2000 longitude"}</dt><dd>{row.longitude_deg.toFixed(4)}°</dd></div>
            <div><dt>Ecliptic latitude</dt><dd>{row.latitude_deg.toFixed(4)}°</dd></div>
            <div><dt>{model==="historical"?"Chapter 12 mean radius":"Distance from Sun"}</dt><dd>{number(row.distance,0)} <small>{model==="historical"?"yojanas":"km"}</small></dd></div>
          </>}
          {model==="historical"&&row.motion_deg_per_day!=null&&body.id!=="Earth"&&<div><dt>Estimated longitude motion</dt><dd>{row.motion_deg_per_day<0?"Retrograde":"Forward"}<small> · {number(Math.abs(row.motion_deg_per_day),4)}°/day</small></dd></div>}
          {model==="modern"&&body.id==="Moon"&&snapshot.bodies.Earth&&<div><dt>Distance from Earth</dt><dd>{number(Math.hypot(...row.position.map((v,i)=>v-snapshot.bodies.Earth.position[i])),0)} <small>km</small></dd></div>}
        </dl>
        <p>Longitude measures direction around the reference plane; latitude measures the angle above or below it. Historical sidereal longitude uses the text’s stellar reference. J2000 is the fixed reference orientation used by this modern view.</p>
        <details className="universe-provenance"><summary>Calculation details</summary><dl>
          <div><dt>Frame</dt><dd>{snapshot.frame}</dd></div><div><dt>Time scale</dt><dd>{snapshot.time_scale}</dd></div>
          <div><dt>Target</dt><dd>{row.target_kind.replace(/_/g," ")}</dd></div>
          <div><dt>Velocity units</dt><dd>{snapshot.velocity_units}</dd></div>
        </dl><p>{snapshot.provenance}</p><p>Numerical values are exact evaluations at the timestamp above. The moving scene interpolates between samples. Screen distances and surface orientation are illustrative.</p></details>
        </details>
      </>:<p className="universe-fact-caption" role="status">Calculating the selected instant…</p>}
    </section>
    {body.kind!=="node"&&<details className="universe-modern-facts universe-provenance"><summary>Modern measurements</summary><p>Sidereal rotation means one full turn relative to distant stars. It differs from the interval between two noons.</p><dl className="universe-values">
      {body.diameter_km!=null&&<div><dt>{body.id==="Sun"?"Approx. diameter":"Equatorial diameter"}</dt><dd>{number(body.diameter_km,0)} <small>km</small></dd></div>}
      {body.rotation_hours!=null&&<div><dt>Sidereal rotation</dt><dd>{number(Math.abs(body.rotation_hours))} <small>hours{body.rotation_hours<0?" · retrograde":""}</small></dd></div>}
      {body.orbital_days!=null&&<div><dt>{body.id==="Moon"?"Orbit around Earth":"Orbit around Sun"}</dt><dd>≈ {number(body.orbital_days,1)} <small>days</small></dd></div>}
      {body.tilt_deg!=null&&<div><dt>Axial tilt</dt><dd>{body.tilt_deg}°</dd></div>}
    </dl><p className="universe-fact-caption">Surface spin is a teaching illustration, not a precise orientation for this date.</p></details>}
    <button type="button" className="universe-ask-about" onClick={onAsk}>Ask Surya about {body.id} <span aria-hidden="true">↗</span></button>
    <details className="universe-provenance"><summary>Sources & further reading</summary><ul>{body.sources.map(source=><li key={source.url}>{source.url.startsWith("/")?<Link to={source.url}>{source.label}</Link>:<a href={source.url} target="_blank" rel="noreferrer">{source.label} ↗</a>}</li>)}</ul></details>
  </div>;
}
