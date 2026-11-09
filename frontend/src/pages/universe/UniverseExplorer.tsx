import { useEffect, useMemo, useRef, useState } from "react";
import type { KeyboardEvent } from "react";
import { explorerApi } from "./explorerApi";
import { ExplorerChat } from "./ExplorerChat";
import { HISTORICAL_ORDER, MODERN_ORDER, modelLabel } from "./math";
import { PlanetDetails } from "./PlanetDetails";
import { Timeline } from "./Timeline";
import { TourCard } from './TourCard';
import { RetrogradeChart } from './RetrogradeChart';
import { makeTours } from "./tours";
import { UniverseMap } from "./UniverseMap";
import { UniverseScene, webglAvailable } from "./UniverseScene";
import { useSimulation } from "./useSimulation";
import type { CameraPose, Catalog, MarsLesson, Model, SimulationState, TourId } from "./types";
import "./universe.css";

export function UniverseExplorer() {
  const simulation=useSimulation();
  const {state,update,snapshot,buffering,error}=simulation;
  const [catalog,setCatalog]=useState<Catalog|null>(null),[catalogError,setCatalogError]=useState("");
  const [catalogRetry,setCatalogRetry]=useState(0);
  const [view,setView]=useState<"3d"|"2d">(()=>webglAvailable()?"3d":"2d");
  const [tab,setTab]=useState<"details"|"chat">("details");
  const [notice,setNotice]=useState("");
  const [offset,setOffset]=useState(-new Date().getTimezoneOffset()/60);
  const [narrow,setNarrow]=useState(()=>window.matchMedia("(max-width:1023px)").matches);
  const [focus,setFocus]=useState<string|null>(null),[reset,setReset]=useState(0);
  const [tour,setTour]=useState<{id:TourId;step:number}|null>(null);
  const [lesson,setLesson]=useState<MarsLesson|null>(null),[lessonError,setLessonError]=useState(''),[lessonRetry,setLessonRetry]=useState(0);
  const cameraState=useRef<CameraPose|null>(null),restoreCamera=useRef<CameraPose|null>(null);
  const beforeTour=useRef<{state:SimulationState;focus:string|null;view:typeof view;tab:typeof tab;offset:number;camera:CameraPose|null}|null>(null);
  const tourTrigger=useRef<HTMLElement|null>(null);
  const root=useRef<HTMLDivElement>(null),panel=useRef<HTMLDivElement>(null);
  const tours=useMemo(()=>makeTours(catalog?.modern_available??false),[catalog?.modern_available]);
  const activeTour=tours.find(t=>t.id===tour?.id),step=activeTour?.steps[tour?.step??0];
  const retrograde=tour?.id==='retrograde';

  useEffect(()=>{
    if(!retrograde||lesson)return;
    const controller=new AbortController();setLessonError('');
    explorerApi.marsLesson(controller.signal).then(setLesson).catch(e=>{if(e.name!=='AbortError')setLessonError(e.message);});
    return()=>controller.abort();
  },[retrograde,lesson,lessonRetry]);

  useEffect(()=>{const previous=document.title;document.title="Universe Explorer · Surya Siddhanta";return()=>{document.title=previous;};},[]);

  useEffect(()=>{
    const controller=new AbortController();setCatalogError("");
    explorerApi.catalog(controller.signal).then(setCatalog).catch(e=>{if(e.name!=="AbortError")setCatalogError(e.message);});
    return()=>controller.abort();
  },[catalogRetry]);
  useEffect(()=>{
    const query=window.matchMedia("(max-width:1023px)");
    const changed=()=>setNarrow(query.matches);
    query.addEventListener("change",changed);return()=>query.removeEventListener("change",changed);
  },[]);

  const bodies=useMemo(()=>{
    if(!catalog)return [];
    return (state.model==="historical"?HISTORICAL_ORDER:MODERN_ORDER)
      .map(id=>catalog.bodies[id]).filter(body=>body&&(state.nodes||body.kind!=="node"));
  },[catalog,state.model,state.nodes]);

  function select(body:string){update({body});setFocus(body);setTab("details");}
  function switchModel(model:Model){
    if(model==="modern"&&!catalog?.modern_available)return;
    let body=state.body;
    if(catalog&&!catalog.bodies[body]?.models.includes(model)){
      setNotice(`${body} is outside the ${model==="historical"?"historical":"modern physical-body"} model. Earth is selected instead.`);body="Earth";
    }else setNotice("");
    update({model,body});setFocus(null);setReset(n=>n+1);
  }
  function applyTour(id:TourId,index:number){
    const target=tours.find(t=>t.id===id);if(!target)return;
    const patch={...target.steps[index].state};
    if(simulation.reducedMotion)patch.playing=false;
    // Replaying begins from the pre-tour instant, not where playback ended.
    if(index===0&&beforeTour.current)patch.timestamp=target.steps[0].state.timestamp??beforeTour.current.state.timestamp;
    update({spin:true,orbiting:true,guides:true,...patch,direction:1});setFocus(patch.body??null);setReset(n=>n+1);setTour({id,step:index});setNotice("");
  }
  function startTour(id:TourId){
    if(!beforeTour.current){beforeTour.current={state:{...state,timestamp:simulation.clock.current},focus,view,tab,offset,camera:cameraState.current};tourTrigger.current=document.activeElement as HTMLElement;}
    applyTour(id,0);
  }
  function exitTour(){
    if(beforeTour.current){restoreCamera.current=beforeTour.current.camera;update(beforeTour.current.state);setFocus(beforeTour.current.focus);setView(beforeTour.current.view);setTab(beforeTour.current.tab);setOffset(beforeTour.current.offset);setReset(n=>n+1);}
    beforeTour.current=null;setTour(null);
    requestAnimationFrame(()=>tourTrigger.current?.focus({preventScroll:true}));
  }
  function failure(){setView("2d");setNotice("3D is unavailable on this device. The 2D map has the same positions, planet details, and time controls.");}
  async function fullscreen(){
    try{if(document.fullscreenElement)await document.exitFullscreen();else await root.current?.requestFullscreen();}
    catch{setNotice("Fullscreen is unavailable in this browser. You can keep exploring in this view.");}
  }
  const body=catalog?.bodies[state.body];
  const timeline=<Timeline state={state} update={update} buffering={buffering} error={error} offset={offset} setOffset={setOffset} tourRange={retrograde?[Date.parse('2024-10-01T00:00Z')/1000,Date.parse('2025-04-01T00:00Z')/1000]:undefined}/>;
  function panelKey(event:KeyboardEvent<HTMLDivElement>){
    if(!["ArrowLeft","ArrowRight","Home","End"].includes(event.key))return;
    event.preventDefault();
    const next=event.key==="Home"?"details":event.key==="End"?"chat":tab==="details"?"chat":"details";
    setTab(next);document.getElementById(`universe-${next}-tab`)?.focus();
  }
  return <div className="universe-page" ref={root}>
    <header className="universe-header"><div><p className="universe-eyebrow">An invitation to wonder · Ch. 1, 2 & 12</p><h1>A universe to explore.</h1><p>Meet the worlds. Move through time. Discover how a model sees the sky.</p></div><span className="universe-header-symbol" aria-hidden="true">☉</span></header>
    <div className="universe-model-bar">
      <div className="universe-model-switch" role="group" aria-label="Astronomical model">
        <button type="button" aria-label="Surya Siddhanta" aria-pressed={state.model==="historical"} onClick={()=>switchModel("historical")}><strong>Surya Siddhanta</strong><span>Earth-centered · historical</span></button>
        <button type="button" aria-label="Modern astronomy" aria-pressed={state.model==="modern"} onClick={()=>switchModel("modern")} disabled={!catalog?.modern_available}><strong>Modern astronomy</strong><span>Sun-centered · JPL DE440</span></button>
      </div>
      <p>One moment.<br/><strong>Two models of motion.</strong></p>
    </div>
    {catalogError&&<div className="universe-feedback" role="alert">{catalogError} <button onClick={()=>setCatalogRetry(n=>n+1)}>Retry catalog</button></div>}
    {catalog&&!catalog.modern_available&&<details className="universe-feedback"><summary>Modern view unavailable · historical exploration is ready</summary><p>{catalog.modern_unavailable_reason}</p><button onClick={()=>{setCatalogRetry(n=>n+1);simulation.retry();}}>Check again</button></details>}
    {notice&&<p className="universe-feedback" role="status">{notice}<button type="button" className="universe-dismiss" aria-label="Dismiss notice" onClick={()=>setNotice("")}>×</button></p>}
    {error&&<div className="universe-feedback is-error" role="alert">{error}<button onClick={simulation.retry}>Retry motion</button></div>}
    <div className="universe-workspace">
      <section className="universe-observatory" aria-label="Universe visualization">
        {tour&&activeTour&&step&&<TourCard tour={activeTour} index={tour.step} reducedMotion={simulation.reducedMotion} onStep={index=>applyTour(tour.id,index)} onExit={exitTour}/>}
        <div className="universe-scene-toolbar"><span><i/>{state.model==="historical"?"Earth at the centre":"Sun at the centre"}</span>
          <div role="group" aria-label="Visualization mode"><button type="button" aria-pressed={view==="3d"} onClick={()=>{if(webglAvailable())setView("3d");else failure();}}>3D view</button><button type="button" aria-pressed={view==="2d"} onClick={()=>setView("2d")}>2D map</button></div>
        </div>
        <div className="universe-scene" aria-busy={buffering}>
          {view==="3d"?<UniverseScene bodies={bodies} model={state.model} selected={state.body} positions={simulation.positions}
            clock={simulation.clock} playing={state.playing} speed={state.speed} direction={state.direction} buffering={buffering}
            trajectories={simulation.trajectories.current} revision={simulation.revision} focus={focus} reset={reset}
            spin={state.spin} orbiting={state.orbiting} guides={state.guides} lesson={retrograde?lesson:null}
            cameraState={cameraState} restoreCamera={restoreCamera}
            reducedMotion={simulation.reducedMotion} onSelect={select} onFailure={failure}/>
            :<UniverseMap bodies={bodies} positions={simulation.positions.current} model={state.model} selected={state.body} guides={state.guides} lesson={retrograde?lesson:null} focus={focus} time={state.timestamp} direction={state.direction} trajectories={simulation.trajectories.current} onSelect={select}/>}
          {buffering&&<div className="universe-loading" role="status"><span/>Preparing this moment…</div>}
          <div className="universe-scene-actions"><button type="button" onClick={()=>{setFocus(null);setReset(n=>n+1);}} aria-label="Reset camera"><span aria-hidden="true">↺</span> Overview</button><button type="button" onClick={fullscreen} aria-label="Toggle fullscreen"><span aria-hidden="true">⛶</span></button></div>
          <p className="universe-scene-hint">{view==="3d"?"Drag to look around · scroll or pinch to zoom":"Top-down map · select a world below"}</p>
        </div>
        <div className="universe-motion-controls" role="group" aria-label="Motion controls"><label><input type="checkbox" checked={state.spin} onChange={e=>update({spin:e.target.checked})}/> Surface spin</label><label><input type="checkbox" checked={state.orbiting} onChange={e=>update({orbiting:e.target.checked})}/> Orbital motion</label><label><input type="checkbox" checked={state.guides} onChange={e=>update({guides:e.target.checked})}/> Motion guides</label></div>
        {state.guides&&<p className="universe-guide-legend">Axis line: spin · curved arrow: surface rotation · straight arrow: positional direction{view==='2d'?' · surface spin is shown in 3D':''}</p>}
        <div className="universe-body-picker" role="group" aria-label="Select a celestial body">{bodies.map(b=><button type="button" key={b.id} aria-label={`Select ${b.id}`} aria-pressed={state.body===b.id} onClick={()=>select(b.id)}><span style={{background:b.color}}/>{b.id}</button>)}</div>
        <div className="universe-scene-notes"><p>Sizes and distances are illustrative. Faint trails show sampled directions.</p><p>{state.model==="historical"?"Surface spin is a modern illustration; Earth’s position stays fixed.":"Surface orientation is illustrative; orbital positions use DE440."} Spin speed is adjusted for visibility.</p>
          {state.model==="historical"&&<label><input type="checkbox" checked={state.nodes} onChange={e=>{const nodes=e.target.checked;update({nodes,...(!nodes&&["Rahu","Ketu"].includes(state.body)?{body:"Moon"}:{})});if(!nodes&&["Rahu","Ketu"].includes(state.body))setFocus("Moon");}}/> Show Rahu & Ketu · crossing directions, not planets</label>}
        </div>
        {retrograde&&(lesson?<RetrogradeChart lesson={lesson} time={state.timestamp} onJump={timestamp=>update({timestamp,playing:false})}/>:lessonError?<div className="universe-feedback" role="alert">{lessonError}<button type="button" onClick={()=>setLessonRetry(n=>n+1)}>Retry lesson chart</button></div>:<p className="universe-scene-notes" role="status">Preparing the historical Mars chart…</p>)}
      </section>
      {narrow&&timeline}
      <aside className="universe-side-panel" ref={panel} aria-label="Planet information and AI companion">
        <div className="universe-panel-tabs" role="tablist" aria-label="Planet panel" onKeyDown={panelKey}><button id="universe-details-tab" type="button" role="tab" tabIndex={tab==="details"?0:-1} aria-selected={tab==="details"} aria-controls="universe-details-panel" onClick={()=>setTab("details")}>Planet details</button><button id="universe-chat-tab" type="button" role="tab" tabIndex={tab==="chat"?0:-1} aria-selected={tab==="chat"} aria-controls="universe-chat-panel" onClick={()=>setTab("chat")}>Ask Surya <span aria-hidden="true">✳</span></button></div>
        <div role="tabpanel" id="universe-details-panel" aria-labelledby="universe-details-tab" hidden={tab!=="details"}>{body?<PlanetDetails body={body} snapshot={snapshot} model={state.model} sceneTime={state.timestamp} onAsk={()=>setTab("chat")}/>:<p className="universe-panel-loading" role="status">Getting to know the worlds…</p>}</div>
        <div role="tabpanel" id="universe-chat-panel" aria-labelledby="universe-chat-tab" hidden={tab!=="chat"}><ExplorerChat state={state} onTour={startTour}/></div>
      </aside>
    </div>
    {!narrow&&timeline}
    <section className="universe-tours" aria-label="Guided tours">
      <div className="universe-tour-heading"><div><p className="universe-eyebrow">Follow your curiosity</p><h2>A little guidance. A big discovery.</h2></div><span>Four short journeys</span></div><div className="universe-tour-list">{tours.map((t,i)=><button type="button" key={t.id} onClick={()=>startTour(t.id)}><span className="universe-tour-number">0{i+1}</span><strong>{t.title}</strong><span>{t.summary}</span><span className="universe-tour-arrow" aria-hidden="true">↗</span></button>)}</div>
    </section>
    <p className="universe-credits">Planet maps: <a href="https://www.solarsystemscope.com/textures/" target="_blank" rel="noreferrer">Solar System Scope / INOVE</a> · <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="noreferrer">CC BY 4.0</a> · Maps use enhanced colors and reconstructed terrain. No live imagery.</p>
  </div>;
}
