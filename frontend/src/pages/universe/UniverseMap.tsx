import { scenePosition, globeSize, sampleAt } from "./math";
import { focusFrame, placeLabels } from './learningMath';
import type { BodyInfo, MarsLesson, Model, Positions, Trajectory } from "./types";

export function UniverseMap({bodies,positions,model,selected,guides,lesson,focus,time,direction,trajectories,onSelect}: {
  bodies:BodyInfo[];positions:Positions;model:Model;selected:string;onSelect:(id:string)=>void;
  guides:boolean;lesson:MarsLesson|null;focus:string|null;time:number;direction:number;trajectories:Trajectory[];
}) {
  const p=scenePosition(selected,positions,model),centre=selected==='Moon'?scenePosition('Earth',positions,model):[0,0,0];
  const frame=focusFrame(p,centre),width=focus?Math.max(10,frame.distance*1.8):70,height=width/1.4;
  const left=(focus?frame.target[0]:0)-width/2,top=(focus?frame.target[2]*.75:0)-height/2,font=width/70*.95;
  const markers=guides&&lesson&&model==='historical'?lesson.samples.filter(s=>['2024-10-01','2025-01-01','2025-04-01'].some(d=>s.instant.startsWith(d))).map(s=>{const a=s.longitude_deg*Math.PI/180;return {id:s.instant.slice(0,10),x:Math.cos(a)*14.6,y:-Math.sin(a)*14.6*.75};}):[];
  const labels=placeLabels([...bodies.map(body=>{const [x,,z]=scenePosition(body.id,positions,model);return {id:body.id,x:(x-left)/width*700,y:(z*.75+globeSize(body.id)+font*1.5-top)/width*700};}),...markers.map(m=>({id:m.id,x:(m.x-left)/width*700,y:(m.y-1-top)/width*700}))],selected,700,500);
  const window=trajectories.find(w=>time>=w.samples[0].timestamp&&time<=w.samples[w.samples.length-1].timestamp);
  const next=window?sampleAt(window.samples,time+3600*direction):null;
  const future=next?scenePosition(selected,next,model):null;
  const tangent=future?[future[0]-p[0],(future[2]-p[2])*.75]:[0,0],angle=Math.atan2(tangent[1],tangent[0])*180/Math.PI;
  return <svg className="universe-map" viewBox={`${left} ${top} ${width} ${height}`} role="img" aria-label="Interactive universe map">
    <title>Top-down directions with compressed distances. Select a planet using the buttons below the map.</title>
    <defs><radialGradient id="universe-sun"><stop stopColor="#fff0bc"/><stop offset="1" stopColor="#f6ad48"/></radialGradient></defs>
    {[4,7,10,13,16,20,25,30].map(r=><circle key={r} r={r} fill="none" stroke="currentColor" opacity=".08" strokeWidth=".05"/>)}
    <line x1="-33" x2="33" stroke="currentColor" opacity=".12" strokeWidth=".04"/>
    <line y1="-23" y2="23" stroke="currentColor" opacity=".12" strokeWidth=".04"/>
    {guides&&lesson&&model==='historical'&&<g className="universe-zodiac-map"><ellipse rx="14.6" ry={14.6*.75} fill="none" stroke="currentColor" opacity=".45" strokeWidth=".08"/>{Array.from({length:12},(_,i)=>{const a=i*Math.PI/6;return <text key={i} x={Math.cos(a)*16} y={-Math.sin(a)*16*.75} textAnchor="middle" fontSize={font}>{i*30}°</text>;})}{markers.map(m=>{const dx=labels[m.id].dx*width/700,dy=labels[m.id].dy*width/700;return <g key={m.id}><circle cx={m.x} cy={m.y} r=".16" fill="currentColor"/><line x1={m.x} y1={m.y} x2={m.x+dx} y2={m.y-1+dy} stroke="currentColor" strokeWidth=".04"/><text x={m.x+dx} y={m.y-1+dy} textAnchor="middle" fontSize={font*.85}>{m.id}</text></g>;})}</g>}
    {guides&&future&&Math.hypot(...tangent)>1e-7&&<g transform={`translate(${p[0]} ${p[2]*.75}) rotate(${angle})`} stroke="#b4d1ff" strokeWidth=".13" fill="none"><path d={`M ${globeSize(selected)+.5} 0 h 2 l -.5 -.35 m .5 .35 l -.5 .35`}/></g>}
    {bodies.map(body=>{
      const [x,,z]=scenePosition(body.id,positions,model),r=globeSize(body.id);
      return <g key={body.id} transform={`translate(${x} ${z*.75})`} onClick={()=>onSelect(body.id)} className="universe-map-body">
        {selected===body.id&&<circle r={r+ .45} fill="none" stroke="#4d8bff" strokeWidth=".12"/>}
        {body.id==="Saturn"&&<ellipse rx={r*2} ry={r*.7} fill="none" stroke={body.color} opacity=".7" strokeWidth=".2"/>}
        <circle r={r} fill={body.id==="Sun"?"url(#universe-sun)":body.color} fillOpacity={body.kind==="node"?.35:1}/>
        <text x={labels[body.id].dx*width/700} y={r+font*1.5+labels[body.id].dy*width/700} textAnchor="middle" fill="currentColor" fontWeight={selected===body.id?700:400} fontSize={font}>{body.id}</text>
      </g>;
    })}
    <text x={left+font*2} y={top+height-font*2} fill="currentColor" opacity=".65" fontSize={font*.8}>{model==="historical"?"SS sidereal directions · Earth at centre":"J2000 ecliptic directions · Sun at centre"}</text>
  </svg>;
}
