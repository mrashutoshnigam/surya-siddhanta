import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api";
import type { ChatSource } from "../../api";
import { Markdown } from "../../components/Markdown";
import { iso, modelLabel } from "./math";
import type { Demonstration, SimulationState, TourId } from "./types";

interface SceneContext {body:string;model:SimulationState['model'];instant:string}
interface Message { role:"user"|"assistant"; text:string; context:SceneContext; sources?:ChatSource[]; demonstrations?:Demonstration[] }
const TOURS:TourId[]=["spin","moon","retrograde","models"];

export function ExplorerChat({state,onTour}: {state:SimulationState;onTour:(id:TourId)=>void}) {
  const [messages,setMessages]=useState<Message[]>([]),[input,setInput]=useState("");
  const [loading,setLoading]=useState(false),[error,setError]=useState("");
  const session=useRef<string>(),epoch=useRef(0),mounted=useRef(true),end=useRef<HTMLDivElement>(null);
  const question=useRef<HTMLTextAreaElement>(null);
  useEffect(()=>{mounted.current=true;return()=>{mounted.current=false;epoch.current++;};},[]);
  useEffect(()=>{end.current?.scrollIntoView({block:"nearest",behavior:"instant"});},[messages,loading]);
  useEffect(()=>{if(question.current){question.current.style.height="auto";question.current.style.height=Math.min(question.current.scrollHeight,160)+"px";}},[input]);
  async function send(question=input) {
    const text=question.trim();if(!text||loading)return;
    const generation=epoch.current;
    const context:SceneContext={model:state.model,body:state.body,instant:iso(state.timestamp)};
    setLoading(true);setError("");setInput("");setMessages(m=>[...m,{role:"user",text,context}]);
    try {
      const response=await api.chat({message:text,session_id:session.current,client_now:new Date().toISOString(),
        utc_offset:-new Date().getTimezoneOffset()/60,
        explorer:{...context,beginner:true}});
      if(!mounted.current||generation!==epoch.current)return;
      session.current=response.session_id;
      setMessages(m=>[...m,{role:"assistant",text:response.reply,context,sources:response.sources,
        demonstrations:response.demonstrations?.filter(d=>TOURS.includes(d.id))}]);
    } catch(e) {
      if(!mounted.current||generation!==epoch.current)return;
      const message=e instanceof Error?e.message:"The answer could not be loaded. Try again.";
      setError(/not configured/i.test(message)?"Chat is not configured on this server. You can still explore the planets and guided tours.":message);
      setInput(text);
    } finally {if(mounted.current&&generation===epoch.current)setLoading(false);}
  }
  function reset(){
    epoch.current++;const previous=session.current;session.current=undefined;
    setMessages([]);setInput("");setError("");setLoading(false);
    if(previous)api.chatReset(previous).catch(()=>{});
  }
  return <div className="universe-chat">
    <div className="universe-chat-context"><span className="universe-eyebrow">Your guide to this scene</span><p>{state.body} · {modelLabel(state.model)}</p><time dateTime={iso(state.timestamp)}>Scene: {iso(state.timestamp).slice(0,16).replace('T',' ')} UTC</time><small>Questions use the simulated date. “Today” uses your real current date.</small></div>
    <div className="universe-context-prompts"><button type="button" disabled={loading} onClick={()=>send(`Explain the motion of ${state.body} in this scene in simple terms.`)}>Explain this motion</button><button type="button" disabled={loading} onClick={()=>send(`For ${state.body} at this simulated instant, what changes in the other model? Keep the reference frames distinct.`)}>What changes in the other model?</button></div>
    <div className="universe-chat-log" role="log" aria-label="Conversation with Surya" aria-live="polite" aria-busy={loading}>
      {messages.length===0&&<div className="universe-chat-welcome"><span aria-hidden="true">✳</span><h3>Curiosity belongs here.</h3><p>Ask about a world, a motion, or what the historical text says.</p><div className="universe-chat-starters">
        {[`Explain ${state.body} like I’m new to astronomy.`,"What is the difference between these models?","Why does Mars move backward?"].map(question=><button type="button" key={question} onClick={()=>send(question)}>{question} <span aria-hidden="true">↗</span></button>)}
      </div></div>}
      {messages.map((message,i)=><div key={i} className={`universe-message is-${message.role}`}>
        <span className="universe-message-author">{message.role==="assistant"?"Surya":"You"}</span>
        <p className="universe-message-context">{message.context.body} · {modelLabel(message.context.model)} · {message.context.instant.slice(0,16).replace('T',' ')} UTC</p>
        {message.role==="assistant"?<Markdown>{message.text}</Markdown>:<p>{message.text}</p>}
        {!!message.sources?.length&&<details className="universe-provenance"><summary>Sources for this answer</summary><ul>{message.sources.map((source,index)=><li key={`${source.id}:${index}`}>
          {source.url?.startsWith("https://")?<a href={source.url} target="_blank" rel="noreferrer">{source.label} ↗</a>:source.url?.startsWith("/")?<Link to={source.url}>{source.label}</Link>:source.kind==="verse"&&source.chapter?<Link to={`/book/${source.chapter}`}>{source.label}</Link>:source.label}
        </li>)}</ul></details>}
        {!!message.demonstrations?.length&&<div className="universe-demo-buttons">{message.demonstrations.map(d=><button type="button" key={d.id} onClick={()=>onTour(d.id)}>Show me: {d.label} <span aria-hidden="true">↗</span></button>)}</div>}
      </div>)}
      {loading&&<p className="universe-chat-thinking" role="status">Surya is checking the sources…</p>}<div ref={end}/>
    </div>
    {error&&<p className="universe-inline-error" role="alert">{error}</p>}
    <form noValidate className="universe-chat-form" onSubmit={e=>{e.preventDefault();send();}}>
      <label htmlFor="universe-question" className="universe-eyebrow">Your question</label>
      <textarea ref={question} className="resize-none" id="universe-question" value={input} maxLength={8000} rows={3} onChange={e=>setInput(e.target.value)} placeholder={`What would you like to know about ${state.body}?`} disabled={loading}/>
      <div><button type="button" onClick={reset} disabled={loading||!messages.length}>New conversation</button><button type="submit" className="universe-primary" disabled={loading||!input.trim()} aria-label="Send question">{loading?"Thinking…":"Send"} <span aria-hidden="true">↗</span></button></div>
    </form>
    <p className="universe-fact-caption">AI explanations can be mistaken. Open the sources to explore the evidence.</p>
  </div>;
}
