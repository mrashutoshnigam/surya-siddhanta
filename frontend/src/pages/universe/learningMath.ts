/** Pure teaching/view helpers. No coordinates are compared across models. */
export function unwrapLongitudes(values:number[]):number[] {
  return values.reduce<number[]>((out,value,index)=>{
    out.push(index ? out[index-1]+((value-values[index-1]+540)%360)-180 : value);
    return out;
  },[]);
}
export const clampTime=(time:number,min:number,max:number)=>Math.max(min,Math.min(max,time));
export function speedExplanation(speed:number):string {
  return ({1:'One second moves one second.',3600:'One second moves one hour.',86400:'One second moves one day.',604800:'One second moves one week.',2592000:'One second moves thirty days.'})[speed]??'Time is accelerated.';
}
export function focusFrame(body:number[],centre:number[]) {
  const separation=Math.hypot(...body.map((v,i)=>v-centre[i]));
  return {target:body.map((v,i)=>(v+centre[i])/2) as [number,number,number],distance:Math.max(5,separation*1.35+3)};
}
interface LabelPoint {id:string;x:number;y:number}
export function placeLabels(points:LabelPoint[],selected:string,width:number,height:number) {
  const placed:{x:number;y:number}[]=[],result:Record<string,{dx:number;dy:number}>={};
  const ordered=[...points].sort((a,b)=>Number(b.id===selected)-Number(a.id===selected));
  for(const p of ordered){
    let x=clampTime(p.x,42,Math.max(42,width-42)),y=clampTime(p.y,14,Math.max(14,height-14));
    for(let attempt=0;attempt<24;attempt++){
      const shift=attempt===0?0:(attempt%2?1:-1)*Math.ceil(attempt/2)*23;
      const candidate=clampTime(p.y+shift,14,Math.max(14,height-14));
      if(!placed.some(q=>Math.abs(q.x-x)<84&&Math.abs(q.y-candidate)<22)){y=candidate;break;}
    }
    placed.push({x,y});result[p.id]={dx:x-p.x,dy:y-p.y};
  }
  return result;
}
