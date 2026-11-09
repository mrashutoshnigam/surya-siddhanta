import { Component, useEffect, useMemo, useRef, useState } from "react";
import type { ElementRef, MutableRefObject, ReactNode } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Html, Line, OrbitControls } from "@react-three/drei";
import * as THREE from "three";
import { globeSize, sampleAt, scenePosition } from "./math";
import { focusFrame, placeLabels } from './learningMath';
import type { BodyInfo, CameraPose, MarsLesson, Model, Positions, Trajectory, Vector } from "./types";

interface SceneProps {
  bodies: BodyInfo[]; model: Model; selected: string; positions: MutableRefObject<Positions>;
  playing: boolean; buffering: boolean; speed: number; direction: number;
  clock: MutableRefObject<number>; trajectories: Trajectory[]; revision: number;
  focus: string | null; reset: number; reducedMotion: boolean;
  spin:boolean;orbiting:boolean;guides:boolean;lesson:MarsLesson|null;
  cameraState:MutableRefObject<CameraPose|null>;restoreCamera:MutableRefObject<CameraPose|null>;
  onSelect: (body: string) => void; onFailure: () => void;
}

export function webglAvailable() {
  try {
    const canvas=document.createElement("canvas");
    const context=canvas.getContext("webgl2");
    if (!context) return false;
    context.getExtension("WEBGL_lose_context")?.loseContext();
    return true;
  } catch {return false;}
}

class SceneBoundary extends Component<{children: ReactNode; onFailure:()=>void}, {failed:boolean}> {
  state={failed:false};
  static getDerivedStateFromError(){return {failed:true};}
  componentDidCatch(){this.props.onFailure();}
  render(){return this.state.failed ? <p className="universe-scene-message">Switching to the accessible 2D map…</p> : this.props.children;}
}

function fallbackTexture(body: BodyInfo) {
  const width=128,height=64,bytes=new Uint8Array(width*height*4), base=new THREE.Color(body.color);
  for(let y=0;y<height;y++) for(let x=0;x<width;x++) {
    const i=(y*width+x)*4;
    const n=Math.sin(x*12.9898+y*78.233)*43758.5453;
    let shade=.78+(n-Math.floor(n))*.27;
    if(["Jupiter","Saturn","Uranus","Neptune"].includes(body.id))shade+=Math.sin(y*.65)*.12;
    const land=body.id==="Earth" && Math.sin(x*.12+Math.sin(y*.2)*2)+Math.sin(y*.26)>.8;
    bytes[i]=Math.min(255,(land?.25:base.r)*255*shade);
    bytes[i+1]=Math.min(255,(land?.48:base.g)*255*shade);
    bytes[i+2]=Math.min(255,(land?.28:base.b)*255*shade);bytes[i+3]=255;
  }
  const texture=new THREE.DataTexture(bytes,width,height);
  texture.colorSpace=THREE.SRGBColorSpace;texture.needsUpdate=true;
  return texture;
}

function usePlanetTexture(body: BodyInfo) {
  const fallback=useMemo(()=>fallbackTexture(body),[body.id]);
  const [texture,setTexture]=useState<THREE.Texture>(fallback);
  useEffect(()=>{
    let active=true,loaded:THREE.Texture|undefined;
    if(body.texture) new THREE.TextureLoader().load(body.texture,value=>{
      loaded=value;value.colorSpace=THREE.SRGBColorSpace;
      if(active)setTexture(value);else value.dispose();
    },undefined,()=>{/* Procedural texture remains visible on failure. */});
    return ()=>{active=false;loaded?.dispose();fallback.dispose();};
  },[body.texture,fallback]);
  return texture;
}

function Planet({body,scene}: {body:BodyInfo;scene:SceneProps}) {
  const group=useRef<THREE.Group>(null), surface=useRef<THREE.Mesh>(null);
  const texture=usePlanetTexture(body),radius=globeSize(body.id);
  const sun=body.id==="Sun", node=body.kind==="node";
  const tilt=(body.tilt_deg??0)*Math.PI/180;
  useFrame((_,delta)=>{
    if(group.current)group.current.position.set(...scenePosition(body.id,scene.positions.current,scene.model));
    if(surface.current && scene.spin && scene.playing && !scene.buffering && !scene.reducedMotion && !document.hidden) {
      const period=Math.abs(body.rotation_hours??24)*3600;
      // Below a visible threshold we deliberately demonstrate spin. Above it
      // we cap the rate so fast-forward never turns surfaces into a strobe.
      const rate=Math.min(.8,Math.max(.065,2*Math.PI*scene.speed/period));
      surface.current.rotation.y+=Math.min(delta,.1)*rate*scene.direction;
    }
  });
  const selected=scene.selected===body.id;
  return <group ref={group}>
    <group rotation={[0,0,tilt]}>
      <mesh ref={surface} onClick={e=>{e.stopPropagation();scene.onSelect(body.id);}}
        onPointerOver={e=>{e.stopPropagation();document.querySelector<HTMLCanvasElement>(".universe-scene canvas")?.style.setProperty("cursor","pointer");}}
        onPointerOut={()=>document.querySelector<HTMLCanvasElement>(".universe-scene canvas")?.style.setProperty("cursor","grab")}>
        <sphereGeometry args={[radius,40,28]}/>
        {sun || node ? <meshBasicMaterial map={node?undefined:texture} color={node?body.color:"white"} wireframe={node}/>
          : <meshStandardMaterial map={texture} roughness={.94} metalness={0}/>}
      </mesh>
      {body.id==="Saturn" && <mesh rotation={[-Math.PI/2,0,0]}>
        <ringGeometry args={[radius*1.3,radius*2,96]}/>
        <meshStandardMaterial color="#c7bba0" side={THREE.DoubleSide} transparent opacity={.72}/>
      </mesh>}
      {body.id==="Earth" && <mesh><sphereGeometry args={[radius*1.035,32,24]}/><meshBasicMaterial color="#76a5d8" transparent opacity={.1} side={THREE.BackSide}/></mesh>}
      {scene.guides&&selected&&!node&&<>
        <Line points={[[0,-radius*1.8,0],[0,radius*1.8,0]]} color="#b4d1ff" lineWidth={2}/>
        <SpinArrow radius={radius} direction={scene.direction}/>
      </>}
    </group>
    {sun && <><pointLight intensity={65} distance={160} decay={1}/><mesh><sphereGeometry args={[radius*1.09,32,24]}/><meshBasicMaterial color={body.color} transparent opacity={.07}/></mesh></>}
    {selected && <mesh rotation={[-Math.PI/2,0,0]}><ringGeometry args={[radius*1.3,radius*1.48,64]}/><meshBasicMaterial color="#4d8bff" side={THREE.DoubleSide} transparent opacity={.95}/></mesh>}
  </group>;
}

function SpinArrow({radius,direction}:{radius:number;direction:number}){
  const angle=Math.PI*1.55*direction;
  const arrow=useMemo(()=>new THREE.ArrowHelper(new THREE.Vector3(-Math.sin(angle)*direction,0,-Math.cos(angle)*direction),new THREE.Vector3(Math.cos(angle)*radius*1.65,radius*.65,-Math.sin(angle)*radius*1.65),radius*.4,'#b4d1ff',radius*.3,radius*.2),[radius,direction,angle]);
  useEffect(()=>()=>arrow.dispose(),[arrow]);
  return <><Line points={Array.from({length:35},(_,i)=>{const a=i/34*angle;return [Math.cos(a)*radius*1.65,radius*.65,-Math.sin(a)*radius*1.65] as Vector;})} color="#b4d1ff" lineWidth={2}/><primitive object={arrow}/></>;
}

function Labels({scene}:{scene:SceneProps}){
  const {camera,size}=useThree(),groups=useRef<Record<string,THREE.Group|null>>({}),labels=useRef<Record<string,HTMLSpanElement|null>>({});
  const projected=useMemo(()=>new THREE.Vector3(),[]);
  const entries=[...scene.bodies.map(b=>({id:b.id,body:b.id,position:null as Vector|null})),...(scene.guides&&scene.lesson&&scene.model==='historical'?scene.lesson.samples.filter(s=>['2024-10-01','2025-01-01','2025-04-01'].some(d=>s.instant.startsWith(d))).map(s=>{const a=s.longitude_deg*Math.PI/180;return {id:s.instant.slice(0,10),body:null,position:[14.6*Math.cos(a),-.8,-14.6*Math.sin(a)] as Vector};}):[])];
  useFrame(()=>{
    const points=entries.map(entry=>{
      const p=entry.position??scenePosition(entry.id,scene.positions.current,scene.model);if(entry.body)p[1]+=globeSize(entry.id)+.5;
      groups.current[entry.id]?.position.set(...p);projected.set(...p).project(camera);
      const visible=projected.z<1&&Math.abs(projected.x)<1.1&&Math.abs(projected.y)<1.1;
      const label=labels.current[entry.id];if(label)label.style.visibility=visible?'visible':'hidden';
      return {id:entry.id,x:(projected.x+1)*size.width/2,y:(1-projected.y)*size.height/2};
    });
    const layout=placeLabels(points,scene.selected,size.width,size.height);
    for(const [id,offset] of Object.entries(layout)){const label=labels.current[id];if(label)label.style.transform=`translate(${offset.dx}px, ${offset.dy}px)`;}
  });
  return <>{entries.map(entry=><group key={entry.id} ref={value=>{groups.current[entry.id]=value;}}><Html center zIndexRange={[5,0]} style={{pointerEvents:'none'}}><span ref={value=>{labels.current[entry.id]=value;}} className={`universe-planet-label${scene.selected===entry.id?' is-selected':''}`}>{entry.id}</span></Html></group>)}</>;
}

function DirectionArrow({scene}:{scene:SceneProps}){
  const arrow=useMemo(()=>new THREE.ArrowHelper(new THREE.Vector3(1,0,0),new THREE.Vector3(),2,'#b4d1ff',.5,.3),[]);
  useEffect(()=>()=>{arrow.dispose();},[arrow]);
  useFrame(()=>{
    arrow.visible=false;
    if(!scene.guides)return;
    const time=scene.clock.current,window=scene.trajectories.find(w=>time>=w.samples[0].timestamp&&time<=w.samples[w.samples.length-1].timestamp);
    if(!window)return;
    const later=sampleAt(window.samples,time+3600*scene.direction),earlier=sampleAt(window.samples,time-3600*scene.direction);
    const next=later??earlier;if(!next)return;
    const p=new THREE.Vector3(...scenePosition(scene.selected,scene.positions.current,scene.model)),q=new THREE.Vector3(...scenePosition(scene.selected,next,scene.model));
    const tangent=q.sub(p).multiplyScalar(later?1:-1);if(tangent.length()<1e-7)return;
    tangent.normalize();arrow.position.copy(p).addScaledVector(tangent,globeSize(scene.selected)+.5);arrow.setDirection(tangent);arrow.visible=true;
  });
  return <primitive object={arrow}/>;
}

function Zodiac({lesson}:{lesson:MarsLesson}){
  const radius=14.6;
  return <group>
    <Line points={Array.from({length:181},(_,i)=>[radius*Math.cos(i*Math.PI/90),0,-radius*Math.sin(i*Math.PI/90)] as Vector)} color="#c3cad8" transparent opacity={.35}/>
    {Array.from({length:12},(_,i)=>{const a=i*Math.PI/6;return <group key={i}><Line points={[[Math.cos(a)*(radius-.3),0,-Math.sin(a)*(radius-.3)],[Math.cos(a)*(radius+.3),0,-Math.sin(a)*(radius+.3)]]} color="#c3cad8"/><Html position={[Math.cos(a)*(radius+1),0,-Math.sin(a)*(radius+1)]} center style={{pointerEvents:'none'}}><span className="universe-zodiac-label">{i*30}°</span></Html></group>;})}
    {lesson.samples.filter(s=>['2024-10-01','2025-01-01','2025-04-01'].some(date=>s.instant.startsWith(date))).map(s=>{const a=s.longitude_deg*Math.PI/180;return <group key={s.timestamp} position={[radius*Math.cos(a),0,-radius*Math.sin(a)]}><mesh><sphereGeometry args={[.16,12,12]}/><meshBasicMaterial color="#e8b881"/></mesh></group>;})}
  </group>;
}

function Stars() {
  const coordinates=useMemo(()=>{
    const values=new Float32Array(900*3);let seed=911;
    const rand=()=>{seed=(seed*16807)%2147483647;return seed/2147483647;};
    for(let i=0;i<900;i++){
      const theta=rand()*2*Math.PI,z=rand()*2-1,r=75+rand()*50;
      values.set([Math.sqrt(1-z*z)*Math.cos(theta)*r,z*r,Math.sqrt(1-z*z)*Math.sin(theta)*r],i*3);
    }
    return values;
  },[]);
  return <points><bufferGeometry><bufferAttribute attach="attributes-position" args={[coordinates,3]}/></bufferGeometry><pointsMaterial color="#c3cad8" size={.065} transparent opacity={.55} sizeAttenuation/></points>;
}

function Camera({scene}: {scene:SceneProps}) {
  const controls=useRef<ElementRef<typeof OrbitControls>>(null);
  const {camera,size}=useThree();
  const focus=useRef<string|null>(null), tween=useRef(false), lastTarget=useRef(new THREE.Vector3());
  useEffect(()=>{
    focus.current=scene.focus;tween.current=true;
    const saved=scene.restoreCamera.current;
    if(saved&&controls.current){
      camera.position.set(...saved.position);controls.current.target.set(...saved.target);
      controls.current.update();lastTarget.current.set(...saved.target);tween.current=false;
      scene.restoreCamera.current=null;
    }
  },[scene.focus,scene.reset,scene.model,size.width,size.height]);
  useFrame((_,delta)=>{
    if(!controls.current)return;
    const body=focus.current?scenePosition(focus.current,scene.positions.current,scene.model):[0,0,0];
    const centre=focus.current==='Moon'?scenePosition('Earth',scene.positions.current,scene.model):[0,0,0];
    const framing=focusFrame(body,centre),target=new THREE.Vector3(...(focus.current?framing.target:[0,0,0] as Vector));
    if(tween.current){
      const overview=scene.model==="modern"?new THREE.Vector3(0,27,40):new THREE.Vector3(0,19,29);
      overview.multiplyScalar(Math.max(1,(scene.model==="modern"?1.6:1.4)/(size.width/size.height)));
      const distance=framing.distance*Math.max(1,1.25/(size.width/size.height));
      const desired=focus.current?target.clone().add(new THREE.Vector3(.6,.5,.8).normalize().multiplyScalar(distance)):overview;
      const alpha=scene.reducedMotion?1:1-Math.exp(-delta*5);
      camera.position.lerp(desired,alpha);controls.current.target.lerp(target,alpha);
      if(camera.position.distanceTo(desired)<.03){tween.current=false;lastTarget.current.copy(target);}
    } else if(focus.current){
      camera.position.add(target.clone().sub(lastTarget.current));controls.current.target.copy(target);lastTarget.current.copy(target);
    }
    controls.current.update();
    scene.cameraState.current={position:camera.position.toArray() as Vector,target:controls.current.target.toArray() as Vector};
  });
  return <OrbitControls ref={controls} enableDamping dampingFactor={.09} minDistance={1.5} maxDistance={95} maxPolarAngle={Math.PI*.93}/>;
}

function Paths({scene}: {scene:SceneProps}) {
  const paths=useMemo(()=>{
    const window=scene.trajectories.find(w=>scene.clock.current>=w.samples[0].timestamp && scene.clock.current<=w.samples[w.samples.length-1].timestamp)??scene.trajectories[0];
    if(!window)return [];
    return scene.bodies.filter(b=>b.id!==(scene.model==="historical"?"Earth":"Sun")&&b.kind!=="node").map(body=>({
      id:body.id,color:body.color,points:window.samples.map(s=>scenePosition(body.id,s.positions,scene.model)),
    }));
  },[scene.revision,scene.model,scene.bodies]);
  return <>{paths.map(path=><Line key={path.id} points={path.points} color={path.color} transparent opacity={scene.selected===path.id ? .55:.22} lineWidth={1}/>)}</>;
}

function ContextGuard({onFailure}:{onFailure:()=>void}) {
  const {gl}=useThree();
  useEffect(()=>{
    const canvas=gl.domElement;
    const lost=(event:Event)=>{event.preventDefault();onFailure();};
    canvas.addEventListener("webglcontextlost",lost);
    // R3F intentionally releases a context when the user selects 2D. Remove
    // our listener first so that ordinary cleanup is not reported as failure.
    return()=>canvas.removeEventListener("webglcontextlost",lost);
  },[gl,onFailure]);
  return null;
}

export function UniverseScene(props: SceneProps) {
  return <SceneBoundary onFailure={props.onFailure}>
    <Canvas camera={{position:[0,19,29],fov:46,near:.05,far:400}} dpr={[1,1.5]}
      gl={{antialias:true,alpha:true,powerPreference:"high-performance"}}
      aria-label="Three-dimensional universe. Use the planet buttons for keyboard selection.">
      <ambientLight intensity={.85}/><hemisphereLight args={["#d5deef","#252832",1.05]}/>
      <ContextGuard onFailure={props.onFailure}/><Stars/><Paths scene={props}/><Camera scene={props}/><Labels scene={props}/><DirectionArrow scene={props}/>
      {props.guides&&props.lesson&&props.model==='historical'&&<Zodiac lesson={props.lesson}/>}
      {props.bodies.map(body=><Planet key={body.id} body={body} scene={props}/>)}
    </Canvas>
  </SceneBoundary>;
}
