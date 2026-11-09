import { unwrapLongitudes } from './learningMath';
import type { MarsLesson } from './types';

export function RetrogradeChart({lesson,time,onJump}:{lesson:MarsLesson;time:number;onJump:(time:number)=>void}) {
  const samples=lesson.samples,values=unwrapLongitudes(samples.map(s=>s.longitude_deg));
  const start=samples[0].timestamp,end=samples[samples.length-1].timestamp;
  const min=Math.floor(Math.min(...values)/5)*5-2,max=Math.ceil(Math.max(...values)/5)*5+2;
  const x=(t:number)=>42+(t-start)/(end-start)*466,y=(v:number)=>116-(v-min)/(max-min)*94;
  const nearest=samples.reduce((a,b)=>Math.abs(a.timestamp-time)<Math.abs(b.timestamp-time)?a:b);
  const index=samples.indexOf(nearest),inside=time>=start&&time<=end;
  const markers=['2024-10-01','2025-01-01','2025-04-01'];
  return <div className="universe-retrograde">
    <h3>Mars against the zodiac</h3>
    <p>Follow its direction from Earth. A falling line means longitude is decreasing. The shaded interval shows backward motion.</p>
    <svg viewBox="0 0 530 150" role="img" aria-label="Mars longitude from October 2024 to April 2025">
      <title>Daily Surya Siddhanta longitude, unwrapped across 360 degrees. Shaded segments move backward.</title>
      {samples.slice(1).map((s,i)=>s.motion_deg_per_day<0?<rect key={s.timestamp} x={x(samples[i].timestamp)} y="15" width={Math.max(1,x(s.timestamp)-x(samples[i].timestamp))} height="102" className="universe-chart-retrograde"/>:null)}
      {[min,max].map(v=><g key={v}><line x1="42" x2="508" y1={y(v)} y2={y(v)} stroke="currentColor" opacity=".2"/><text x="2" y={y(v)+4}>{Math.round(v)}°</text></g>)}
      {samples.slice(1).map((s,i)=><line key={s.timestamp} x1={x(samples[i].timestamp)} x2={x(s.timestamp)} y1={y(values[i])} y2={y(values[i+1])} stroke="currentColor" strokeWidth="2"/>)}
      {inside&&<g><line x1={x(time)} x2={x(time)} y1="15" y2="117" className="universe-chart-cursor"/><circle cx={x(nearest.timestamp)} cy={y(values[index])} r="4" fill="currentColor"/></g>}
      {markers.map(date=>{const s=samples.find(s=>s.instant.startsWith(date))!;return <text key={date} x={x(s.timestamp)} y="140" textAnchor={date===markers[0]?'start':date===markers[2]?'end':'middle'}>{date}</text>;})}
    </svg>
    <p className="universe-chart-reading">{inside?`${nearest.instant.slice(0,10)} · ${nearest.longitude_deg.toFixed(2)}° · ${nearest.motion_deg_per_day<0?'Backward in longitude':'Forward in longitude'}`:'The scene is outside this lesson’s date range.'}</p>
    <div className="universe-event-buttons">{markers.map((date,i)=><button key={date} type="button" onClick={()=>onJump(samples.find(s=>s.instant.startsWith(date))!.timestamp)}>{['Before reversal','In retrograde','Forward again'][i]}<small>{date}</small></button>)}</div>
    <details className="universe-provenance"><summary>Chart data & source</summary><p>{lesson.frame} · {lesson.time_scale}. Daily exact evaluations; station dates are not resolved within each day. Longitude is unwrapped only to keep the chart continuous.</p><p>{lesson.provenance}</p><table><caption>Weekly readings and the final day</caption><thead><tr><th scope="col">UTC date</th><th scope="col">Longitude</th><th scope="col">Direction</th></tr></thead><tbody>{samples.filter((_,i)=>i%7===0||i===samples.length-1).map(s=><tr key={s.timestamp}><td>{s.instant.slice(0,10)}</td><td>{s.longitude_deg.toFixed(3)}°</td><td>{s.motion_deg_per_day<0?'Backward':'Forward'}</td></tr>)}</tbody></table></details>
  </div>;
}
