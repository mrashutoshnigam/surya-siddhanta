import { Link } from "react-router-dom";
import { LESSONS } from "./lessons";
import "./learning-lab.css";
export function LearningPaths() {
 return <div className="learning-lab learning-paths">
  <header className="lab-header"><div><p className="lab-eyebrow">Learn / Surya Siddhanta</p><h1>Choose your learning path</h1><p>Start with the Sun, explore the Moon, then follow the planetary corrections. Each experiment connects a date, a diagram and a historical rule.</p></div></header>
  <p className="lesson-intro">Suggested order: Sun → Moon → Mars → Mercury &amp; Venus → Jupiter &amp; Saturn → Rahu. Lessons are open; choose any starting point.</p>
  <ol className="path-list">{LESSONS.map((lesson,i)=><li key={lesson.body}><span className="path-number">{String(i+1).padStart(2,"0")}</span><div><p className="lab-eyebrow">{lesson.body}</p><h2>{lesson.title}</h2><p>{lesson.goal}</p></div>{lesson.ready ? <Link to={`/learn/${lesson.body.toLowerCase()}`}>Explore {lesson.body} →</Link> : <span className="lab-caption">Planned</span>}</li>)}<li><span className="path-number">08</span><div><p className="lab-eyebrow">Rahu</p><h2>Understand nodes and eclipses</h2><p>Follow the ascending node and explain why phase alone does not establish an eclipse.</p></div><Link to="/learn/rahu">Explore Rahu →</Link></li></ol>
  <p className="lab-caption">Diagrams show angular relationships. “True” means corrected within the historical model. Understanding checks offer practice; educational effectiveness has not been measured.</p>
  <Link to="/research">Inspect the saved modern-reference comparison →</Link>
 </div>;
}
