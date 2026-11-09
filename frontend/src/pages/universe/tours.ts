import { DAY } from "./math";
import type { SimulationState, TourId } from "./types";

interface Step { title:string; text:string; state:Partial<SimulationState> }
export interface Tour { id:TourId; title:string; summary:string; steps:Step[] }
export function makeTours(modernAvailable:boolean):Tour[] {
  return [
    {id:"spin",title:"A spin and a journey",summary:"Two motions. Two different stories.",steps:[
      {title:"A globe can turn in place",text:"Watch Earth’s surface turn around its axis. This is a modern illustration: Earth’s position stays fixed in the Surya Siddhanta view. Spin is deliberately made visible, rather than shown at literal speed. Orbital motion is held so you can isolate the turning surface.",state:{model:"historical",body:"Earth",speed:3600,spin:true,orbiting:false,playing:true}},
      {title:"An orbit changes position",text:"Now follow the Sun’s calculated direction around Earth. Surface spin is off: watch its changing direction instead. In this historical model, the displayed path represents calculated directions at an illustrative distance.",state:{model:"historical",body:"Sun",spin:false,orbiting:true,speed:7*DAY,playing:true}},
      {title:modernAvailable?"Change the model":"Keep the ideas separate",text:modernAvailable?"In modern astronomy Earth travels around the Sun while also turning on its axis. The orbital positions now come from JPL, rather than the historical formulas.":"Modern astronomy describes Earth orbiting the Sun. That view needs the optional JPL data file. You can still explore the complete historical model here.",state:{model:modernAvailable?"modern":"historical",body:"Earth",speed:DAY,playing:false}},
    ]},
    {id:"moon",title:"Follow the Moon",summary:"A small world and its nearby companion.",steps:[
      {title:"Find Earth’s companion",text:"The Moon moves around Earth. Here its direction is calculated using the Surya Siddhanta’s longitude and latitude rules. Its displayed size and distance are enlarged so you can follow it.",state:{model:"historical",body:"Moon",speed:DAY,playing:false}},
      {title:"Let a month pass",text:"Press Play, or watch the Moon move as simulated days pass. Its path tilts slightly above and below the ecliptic. The optional Rahu and Ketu markers show crossing directions, not extra worlds.",state:{model:"historical",body:"Moon",nodes:true,speed:DAY,playing:true}},
      {title:modernAvailable?"A journey inside a journey":"What you have seen",text:modernAvailable?"In the modern view the Moon stays near Earth as both travel around the Sun. The Moon’s orbit is enlarged separately so it remains visible.":"The Moon’s calculated direction changes throughout a month. Use the timeline to explore another date, or ask Surya about the lunar nodes.",state:{model:modernAvailable?"modern":"historical",body:"Moon",speed:DAY,playing:false}},
    ]},
    {id:"retrograde",title:"Mars moves backward",summary:"See an apparent reversal in the zodiac.",steps:[
      {title:"Start before the reversal",text:"We have jumped to October 2024. The historical model places Mars by its direction from Earth. The faint trail follows calculated directions; it is not a physical loop in space.",state:{model:"historical",body:"Mars",timestamp:Date.parse("2024-10-01T00:00:00Z")/1000,speed:DAY,playing:false}},
      {title:"Catch Mars in retrograde",text:"On 1 January 2025 the Surya Siddhanta calculation has Mars moving backward in longitude. Check the Retrograde value in Planet details. Play slowly or reverse time to follow it.",state:{model:"historical",body:"Mars",timestamp:Date.parse("2025-01-01T00:00:00Z")/1000,speed:DAY,playing:false}},
      {title:"Forward again",text:"By April the calculated longitude is increasing again. Retrograde describes a change in direction seen from Earth. In modern astronomy it is explained by the relative motion of Earth and Mars around the Sun.",state:{model:"historical",body:"Mars",timestamp:Date.parse("2025-04-01T00:00:00Z")/1000,speed:DAY,playing:false}},
    ]},
    {id:"models",title:"Two ways to see",summary:"Compare the historical and modern models.",steps:[
      {title:"Begin with the historical model",text:"Earth is the centre here. Sun, Moon and five classical planets follow directions computed from the text. The surface textures and their spin are modern teaching illustrations.",state:{model:"historical",body:"Earth",playing:false}},
      {title:modernAvailable?"Now centre the Sun":"Meet the modern view",text:modernAvailable?"The same simulated instant is preserved, but modern positions come from the JPL DE440 ephemeris. Earth is now one of eight planets, with its Moon nearby.":"The Sun-centered view uses a separate modern ephemeris. Its optional data file is not installed here, so this scene remains historical. No historical values are substituted for modern results.",state:{model:modernAvailable?"modern":"historical",body:"Earth",playing:false}},
      {title:"Read the labels",text:"Both views help us learn, but their calculations and reference frames differ. Sizes, distances, and surface spin are adjusted for visibility. Open Calculation details to see the source, frame, and exact result time.",state:{playing:false}},
    ]},
  ];
}
