import { useCallback, useEffect, useRef, useState } from "react";
import { explorerApi } from "./explorerApi";
import { DAY, MIN_TIME, MAX_TIME, sampleAt } from "./math";
import type { Positions, SimulationState, Snapshot, Trajectory } from "./types";

const reducedMotion = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const initialState = (): SimulationState => ({model:"historical", body:"Earth", timestamp:Date.now()/1000,
  playing:!reducedMotion(), speed:1, direction:1, nodes:false,spin:true,orbiting:true,guides:true});
const trajectoryStart = (time:number) => Math.min(MAX_TIME-1,
  Math.max(MIN_TIME, MIN_TIME + Math.floor((time-MIN_TIME)/(32*DAY))*32*DAY));

export function useSimulation() {
  const [state, setState] = useState<SimulationState>(initialState);
  const live = useRef(state);
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [error, setError] = useState("");
  const [buffering, setBuffering] = useState(true);
  const [revision, setRevision] = useState(0);
  const [retry, setRetry] = useState(0);
  const windows = useRef<Trajectory[]>([]);
  const epoch = useRef(0);
  const requests = useRef(new Set<string>());
  const failures = useRef(new Map<string,string>());
  const controllers = useRef(new Set<AbortController>());
  const clock = useRef(state.timestamp);
  const positions = useRef<Positions>({});

  const update = useCallback((patch: Partial<SimulationState>) => {
    const previous = live.current;
    const next = {...previous, ...patch};
    next.timestamp = Math.max(MIN_TIME, Math.min(MAX_TIME, next.timestamp));
    live.current = next;
    if (patch.timestamp !== undefined) {clock.current = next.timestamp;setError("");}
    if (next.model !== previous.model) positions.current = {};
    setState(next);
  }, []);

  // A generation belongs to one model. Date jumps can retain useful windows,
  // but older-model responses are never allowed to replace newer selections.
  useEffect(() => {
    epoch.current++;
    windows.current = [];
    requests.current.clear();
    failures.current.clear();
    controllers.current.forEach(c => c.abort()); controllers.current.clear();
    setSnapshot(null); setError(""); setBuffering(true);
    return () => { epoch.current++; controllers.current.forEach(c => c.abort()); };
  }, [state.model, retry]);

  useEffect(() => {
    let active = true;
    function load(start: number, needed = false) {
      const days = Math.min(32, (MAX_TIME - start) / DAY);
      if (days <= 0) return;
      const key = `${live.current.model}:${start}`;
      const failure = failures.current.get(key);
      if (failure !== undefined) {
        // A previously failed window may become relevant after another jump.
        // Keep its recovery action available instead of buffering forever.
        if (needed) {setError(failure);if(live.current.playing)update({playing:false});}
        return;
      }
      if (requests.current.has(key) || windows.current.some(w => w.samples[0].timestamp === start)) return;
      requests.current.add(key);
      const generation = epoch.current, selectedModel = live.current.model;
      const controller = new AbortController();controllers.current.add(controller);
      explorerApi.trajectory(selectedModel, start, days, controller.signal).then(window => {
        if (!active || generation !== epoch.current) return;
        windows.current = [...windows.current, window].sort((a,b) =>
          Math.abs(a.samples[0].timestamp-clock.current)-Math.abs(b.samples[0].timestamp-clock.current)).slice(0,4);
        if (selectedModel === live.current.model && trajectoryStart(clock.current) === start) setError("");
        setRevision(n=>n+1);
      }).catch(e => {
        if (active && generation === epoch.current && e.name !== "AbortError") {
          failures.current.set(key,e.message);
          // Date jumps share a model generation so useful windows stay cached.
          // A late error from an old date or unused prefetch must stay local.
          if (selectedModel === live.current.model && trajectoryStart(clock.current) === start) {
            setError(e.message);if(live.current.playing)update({playing:false});
          }
        }
      }).finally(() => {requests.current.delete(key);controllers.current.delete(controller);});
    }
    // Fixed 32-day windows share cache entries across clients. A one-second
    // overlap at the upper supported boundary avoids an uncovered final tick.
    const check = () => {
      const time = clock.current;
      const current = trajectoryStart(time);
      load(current,true);
      const next = current + live.current.direction*32*DAY;
      const remaining = live.current.direction===1 ? current+32*DAY-time : time-current;
      if (live.current.playing && remaining<Math.max(live.current.speed*4,DAY) && next >= MIN_TIME && next < MAX_TIME) load(next);
    };
    check(); const timer = window.setInterval(check, 400);
    return () => {active=false;window.clearInterval(timer);};
  }, [state.model, retry, update]);

  useEffect(() => {
    let frame = 0, last = performance.now(), lastPublish = 0, wasBuffering = true;
    const tick = (now: number) => {
      const delta = Math.min((now-last)/1000, .15); last=now;
      const current = live.current;
      const candidate = current.playing && current.orbiting && !document.hidden
        ? Math.max(MIN_TIME, Math.min(MAX_TIME, clock.current+delta*current.speed*current.direction)) : clock.current;
      const window = windows.current.find(w => w.model === current.model && candidate >= w.samples[0].timestamp && candidate <= w.samples[w.samples.length-1].timestamp);
      const values = window ? sampleAt(window.samples,candidate) : null;
      const waiting = values === null;
      if (values) {clock.current=candidate;positions.current=values;}
      else if (current.playing) {
        // Playback can reach a failed prefetch before the clock itself enters
        // that window. Surface the error only once this next frame needs it.
        const failure=failures.current.get(`${current.model}:${trajectoryStart(candidate)}`);
        if(failure!==undefined){setError(failure);update({playing:false});}
      }
      if (waiting !== wasBuffering) {setBuffering(waiting);wasBuffering=waiting;}
      if (now-lastPublish>150) {
        live.current={...live.current,timestamp:clock.current};setState(live.current);lastPublish=now;
        if ((candidate === MIN_TIME || candidate === MAX_TIME) && current.playing) update({playing:false});
      }
      frame=requestAnimationFrame(tick);
    };
    frame=requestAnimationFrame(tick);
    const visibility=()=>{if(document.hidden) update({playing:false});};
    document.addEventListener("visibilitychange",visibility);
    return ()=>{cancelAnimationFrame(frame);document.removeEventListener("visibilitychange",visibility);};
  }, [update]);

  // Exact details follow explicit changes, pause, and a low-rate live refresh.
  // A request belongs to its captured instant/model; cancellation prevents
  // stale network responses from overwriting a later date or model selection.
  const snapshotBucket = state.playing ? Math.floor(state.timestamp / Math.max(state.speed*3,3)) : state.timestamp;
  useEffect(() => {
    const controller=new AbortController();
    const time=clock.current, selectedModel=state.model;
    const timer=window.setTimeout(()=>{
      explorerApi.snapshot(selectedModel,time,controller.signal).then(value=>{
        if (!controller.signal.aborted && selectedModel === live.current.model) setSnapshot(value);
      }).catch(e=>{if(e.name!=="AbortError")setError(e.message);});
    }, state.playing ? 300 : 80);
    return ()=>{window.clearTimeout(timer);controller.abort();};
  }, [state.model, state.playing, snapshotBucket, retry]);

  return {state, update, clock, positions, snapshot, buffering, error, revision,
    trajectories:windows, retry:()=>{setRetry(n=>n+1);}, reducedMotion:reducedMotion()};
}
