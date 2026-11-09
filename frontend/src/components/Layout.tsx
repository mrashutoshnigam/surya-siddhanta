import { NavLink, Outlet, useLocation } from "react-router-dom";
import { GlossaryPanel } from "../glossary/GlossaryPanel";
import { GlossaryProvider } from "../glossary/GlossaryProvider";
import { BOOK_CHAPTERS } from "../pages/book/BookChapter";
import { ThemeToggle } from "./ThemeToggle";
import { ProjectWelcome } from "./ProjectWelcome";

const NAV = [
  {
    group: "Learn",
    items: [{ to: "/learn", label: "Learning Paths" }, { to: "/research", label: "Research Explorer" }],
  },
  {
    group: "Explorer",
    items: [
      { to: "/positions", label: "Planet Positions" },
      { to: "/panchanga", label: "Panchanga" },
      { to: "/eclipse/lunar", label: "Lunar Eclipse" },
      { to: "/eclipse/solar", label: "Solar Eclipse" },
      { to: "/conjunctions", label: "Conjunctions" },
      { to: "/stars", label: "Stars" },
      { to: "/heliacal", label: "Heliacal Events" },
      { to: "/moon", label: "Moon" },
      { to: "/patas", label: "Patas" },
      { to: "/cosmography", label: "Cosmography" },
      { to: "/instruments", label: "Instruments" },
      { to: "/place-time", label: "Place & Time" },
    ],
  },
  {
    group: "Almanac",
    items: [{ to: "/daily-panchanga", label: "Daily Panchanga" }],
  },
  {
    group: "AI",
    items: [{ to: "/chat", label: "Surya Siddhanta AI" }],
  },
];

export function Layout() {
  const pathname = useLocation().pathname;
  const isLearning = pathname === "/learn" || pathname.startsWith("/learn/");
  const isResearch = pathname === "/research";
  return (
    <GlossaryProvider>
      <div className={"app-shell" + (isLearning ? " learning-shell" : isResearch ? " research-shell" : "")}>
        <nav className="sidebar">
          {(isLearning || isResearch) && <a className="lab-skip" href="#learning-content">Skip to the {isResearch ? "research" : "experiment"} ↓</a>}
          <div className="brand">Surya Siddhanta</div>
          <p className="brand-caption">
            Planetary positions, eclipses, conjunctions, stars &amp; the almanac — computed from Surya
            Siddhanta algorithms (Ch.1–14).
          </p>
          {NAV.map((section) => (
            <div key={section.group} className="nav-group">
              <div className="nav-group-title">{section.group}</div>
              {section.items.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}
                >
                  {item.label}
                </NavLink>
              ))}
            </div>
          ))}

          {/* The book comes last: the task pages are the everyday entry
              points, and the chapter list is the long reference behind them. */}
          <div className="nav-group">
            <div className="nav-group-title">The Book</div>
            {/* All fourteen chapters, so the menu is the book's own table of
                contents; the ones without verse cards yet are shown inert. */}
            {BOOK_CHAPTERS.map((chapter) =>
              chapter.ready ? (
                <NavLink
                  key={chapter.number}
                  to={`/book/${chapter.number}`}
                  className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}
                  title={chapter.title}
                >
                  {chapter.number}. {chapter.title}
                </NavLink>
              ) : (
                <span key={chapter.number} className="nav-link nav-link-soon" title={chapter.title}>
                  {chapter.number}. {chapter.title}
                  <em>soon</em>
                </span>
              ),
            )}
          </div>

          <div className="sidebar-footer">suryasiddhanta · default location Ujjain</div>
        </nav>
        <main className="content" id="learning-content">
          <ThemeToggle />
          <Outlet />
          <footer className="legal-band">
            <ProjectWelcome isHome={pathname === "/" || pathname === "/positions"} />
            <span>Ashutosh Nigam</span>
            <span className="legal-sep">·</span>
            <span className="legal-roll">Roll No: M25AI2006</span>
            <span className="legal-sep">·</span>
            <span>
              {isLearning || isResearch ? "SS calculations · separate saved DE440 comparison" : "Computed from the Surya Siddhanta (Burgess, 1860) — no external ephemeris"}
            </span>
          </footer>
        </main>
        {/* Outside <main>: the panel never reflows the page, and the page
            scan (which watches main.content) never sees the panel. */}
        <GlossaryPanel />
      </div>
    </GlossaryProvider>
  );
}
