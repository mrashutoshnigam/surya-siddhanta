import { useRef, useState } from "react";
import { DAY, formatClock, MAX_TIME, MIN_TIME, parseClock } from "./math";
import type { SimulationState } from "./types";
import { clampTime, speedExplanation } from './learningMath';

const SPEEDS = [[1,"Real time"],[3600,"1 hour / second"],[DAY,"1 day / second"],[7*DAY,"7 days / second"],[30*DAY,"30 days / second"]] as const;
export function zoneLabel(offset:number){
  const hours=Math.floor(Math.abs(offset)),minutes=Math.round((Math.abs(offset)-hours)*60);
  return `UTC${offset<0?"−":"+"}${String(hours).padStart(2,"0")}:${String(minutes).padStart(2,"0")}`;
}

export function Timeline({state,update,buffering,error,offset,setOffset,tourRange}: {
  state:SimulationState;update:(patch:Partial<SimulationState>)=>void;buffering:boolean;error:string;
  offset:number;setOffset:(offset:number)=>void;
  tourRange?:[number,number];
}) {
  const [draft,setDraft]=useState(formatClock(state.timestamp,offset));
  const [dirty,setDirty]=useState(false),[invalid,setInvalid]=useState("");
  const dateInput=useRef<HTMLInputElement>(null);
  const browserOffset=-new Date().getTimezoneOffset()/60;
  const range=tourRange??[Math.max(MIN_TIME,state.timestamp-16*DAY),Math.min(MAX_TIME,state.timestamp+16*DAY)];
  const scrubRange=useRef(range);
  const [scrubbing,setScrubbing]=useState(false);
  const bounds=scrubbing?scrubRange.current:range;
  function jump(){
    const timestamp=parseClock(dirty?draft:formatClock(state.timestamp,offset),offset);
    if(timestamp===null){setInvalid("Choose a valid date and time between 1550 and 2649 CE (UTC).");dateInput.current?.focus();return;}
    setInvalid("");setDirty(false);update({timestamp,playing:false});
  }
  return <section className="universe-timeline" aria-label="Simulation time controls">
    <div className="universe-time-heading">
      <span className="universe-eyebrow">Time machine</span>
      <time dateTime={new Date(state.timestamp*1000).toISOString()}>{formatClock(state.timestamp,offset).replace("T"," · ")} <small>{zoneLabel(offset)}</small></time>
      <span className="universe-time-state" role="status">{buffering?"Preparing motion…":state.playing?`${state.orbiting?(state.direction<0?"Rewinding":"Playing"):"Orbital motion held"} · ${SPEEDS.find(s=>s[0]===state.speed)?.[1]}`:"Paused"}</span>
    </div>
    <div className="universe-time-controls">
      <div className="universe-playback">
        <button type="button" aria-label="Step backward one day" disabled={state.timestamp<=MIN_TIME} onClick={()=>update({timestamp:clampTime(state.timestamp-DAY,MIN_TIME,MAX_TIME),playing:false})}>−1 day</button>
        <button type="button" className="universe-play" onClick={()=>update({playing:!state.playing})} disabled={!!error} aria-label={state.playing?"Pause simulation":"Play simulation"}>
          <span aria-hidden="true">{state.playing?"Ⅱ":"▶"}</span>{state.playing?"Pause":"Play"}
        </button>
        <button type="button" aria-label="Step forward one day" disabled={state.timestamp>=MAX_TIME} onClick={()=>update({timestamp:clampTime(state.timestamp+DAY,MIN_TIME,MAX_TIME),playing:false})}>+1 day</button>
        <button type="button" aria-pressed={state.direction<0} onClick={()=>update({direction:state.direction===1?-1:1})}><span aria-hidden="true">↶</span> Reverse</button>
        <button type="button" onClick={()=>{setDirty(false);setInvalid("");update({timestamp:Date.now()/1000,speed:1,direction:1,playing:false});}}>Now</button>
      </div>
      <label>Speed<select aria-label="Speed" value={state.speed} onChange={e=>update({speed:Number(e.target.value)})}>{SPEEDS.map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></label>
      <form noValidate className="universe-date-jump" onSubmit={e=>{e.preventDefault();jump();}}>
        <label>Date and time<input ref={dateInput} aria-label="Date and time" type="datetime-local" value={dirty?draft:formatClock(state.timestamp,offset)}
          min={formatClock(MIN_TIME,offset)} max={formatClock(MAX_TIME,offset)} step="60"
          onChange={e=>{setDraft(e.target.value);setDirty(true);}} aria-invalid={!!invalid} aria-describedby={invalid?"universe-date-error":"universe-date-range"}/></label>
        <button type="submit">Go to date</button>
      </form>
      <label>Timezone<select aria-label="Timezone" value={offset} onChange={e=>{setOffset(Number(e.target.value));setDirty(false);setInvalid("");}}>
        {[...new Set([browserOffset,0,5.5])].map(zone=><option key={zone} value={zone}>{zoneLabel(zone)}{zone===browserOffset?" · your zone":""}</option>)}
      </select></label>
    </div>
    <div className="universe-scrubber"><label htmlFor="universe-date-scrub">{tourRange?'Explore tour date':'Explore nearby dates'}</label>
      <input id="universe-date-scrub" type="range" min={bounds[0]} max={bounds[1]} step={DAY/24} value={clampTime(state.timestamp,bounds[0],bounds[1])}
        aria-valuetext={formatClock(state.timestamp,offset).replace('T',' ')+' '+zoneLabel(offset)}
        onPointerDown={()=>{scrubRange.current=range;setScrubbing(true);}} onPointerUp={()=>setScrubbing(false)} onPointerCancel={()=>setScrubbing(false)}
        onFocus={()=>{scrubRange.current=range;setScrubbing(true);}} onBlur={()=>setScrubbing(false)}
        onChange={e=>{setDirty(false);setInvalid('');update({timestamp:Number(e.target.value),playing:false});}}/>
      <div><span>{formatClock(bounds[0],offset).slice(0,10)}</span><span>{formatClock(bounds[1],offset).slice(0,10)}</span></div>
    </div>
    <p className="universe-fact-caption">{speedExplanation(state.speed)}{!state.orbiting?' Orbital motion is held; enable it to advance the scene date.':''}</p>
    <p id="universe-date-range" className="universe-date-range">Gregorian calendar · 1550–2649 CE (UTC)</p>
    {invalid&&<p id="universe-date-error" className="universe-inline-error" role="alert">{invalid}</p>}
  </section>;
}
