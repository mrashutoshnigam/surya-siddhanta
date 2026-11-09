import { useEffect, useRef } from 'react';
import type { Tour } from './tours';

export function TourCard({tour,index,reducedMotion,onStep,onExit}:{tour:Tour;index:number;reducedMotion:boolean;onStep:(index:number)=>void;onExit:()=>void}){
  const heading=useRef<HTMLHeadingElement>(null),card=useRef<HTMLElement>(null),step=tour.steps[index];
  useEffect(()=>{heading.current?.focus({preventScroll:true});card.current?.scrollIntoView({block:'start',behavior:'instant'});},[tour.id,index]);
  return <section ref={card} className="universe-tour-active" aria-label="Active guided tour">
    <div className="universe-tour-progress"><span>{tour.title} · Step {index+1} of {tour.steps.length}</span><button type="button" aria-label="Exit tour" onClick={onExit}>Exit tour</button></div>
    <h2 ref={heading} tabIndex={-1}>{step.title}</h2><p>{step.text}</p>
    {reducedMotion&&step.state.playing&&<p className="universe-fact-caption">Motion starts paused for your reduced-motion preference. Press Play to explore at your own pace.</p>}
    <div className="universe-tour-controls"><button type="button" disabled={index===0} aria-label="Previous step" onClick={()=>onStep(index-1)}>Back</button><button type="button" aria-label="Replay tour" onClick={()=>onStep(0)}>Replay</button>{index<tour.steps.length-1?<button type="button" className="universe-primary" aria-label="Next step" onClick={()=>onStep(index+1)}>Next step</button>:<button type="button" className="universe-primary" onClick={onExit}>Finish tour</button>}</div>
  </section>;
}
