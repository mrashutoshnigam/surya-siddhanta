import { useEffect, useRef, useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { GlossaryPanel } from "../glossary/GlossaryPanel";
import { GlossaryProvider } from "../glossary/GlossaryProvider";
import { BOOK_CHAPTERS } from "../pages/book/BookChapter";
import { ThemeToggle } from "./ThemeToggle";
import { ProjectWelcome } from "./ProjectWelcome";
import { ChatPanel } from "./ChatPanel";

const NAV = [
  {
    group: "Learn",
    items: [{ to: "/universe", label: "Universe Explorer" }, { to: "/learn", label: "Learning Paths" }, { to: "/research", label: "Research Explorer" }],
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
];

export function Layout() {
  const location = useLocation();
  const pathname = location.pathname;
  const navigate = useNavigate();
  const isLearning = pathname === "/learn" || pathname.startsWith("/learn/");
  const isResearch = pathname === "/research";
  const isUniverse = pathname === "/universe";
  const [universeMenuOpen, setUniverseMenuOpen] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);
  const [glossaryRequest, setGlossaryRequest] = useState(0);
  const chatTriggerRef = useRef<HTMLButtonElement>(null);

  // Keep old /chat bookmarks useful without maintaining a second conversation.
  useEffect(() => {
    if (!location.state?.openChat) return;
    setChatOpen(true);
    navigate(location.pathname + location.search + location.hash, { replace: true, state: null });
  }, [location, navigate]);

  function closeChat() {
    setChatOpen(false);
    requestAnimationFrame(() => chatTriggerRef.current?.focus({ preventScroll: true }));
  }
  return (
    <GlossaryProvider>
      <div className={"app-shell" + (chatOpen ? " chat-open" : "") + (isLearning ? " learning-shell" : isResearch ? " research-shell" : isUniverse ? " universe-shell" : "")}>
        <nav className={"sidebar" + (universeMenuOpen ? " universe-menu-open" : "")}>
          {(isLearning || isResearch || isUniverse) && <a className="lab-skip" href="#learning-content">Skip to the {isUniverse ? "universe" : isResearch ? "research" : "experiment"} ↓</a>}
          <div className="brand">Surya Siddhanta</div>
          {isUniverse && <button type="button" className="universe-mobile-menu-toggle" aria-expanded={universeMenuOpen} onClick={() => setUniverseMenuOpen(open => !open)}>{universeMenuOpen ? "Close menu ×" : "All tools ☰"}</button>}
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

          <div className="nav-group">
            <div className="nav-group-title">AI</div>
            <button
              ref={chatTriggerRef}
              type="button"
              className={"nav-link chat-nav-trigger" + (chatOpen ? " active" : "")}
              aria-expanded={chatOpen}
              aria-controls="chat-panel"
              onClick={() => chatOpen ? closeChat() : setChatOpen(true)}
            >
              Surya Siddhanta AI
            </button>
          </div>

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
        <main className="content" id="learning-content" tabIndex={isUniverse ? -1 : undefined}>
          <ThemeToggle />
          <Outlet />
          <footer className="legal-band">
            <ProjectWelcome isHome={pathname === "/" || pathname === "/positions"} />
            <span>Ashutosh Nigam</span>
            <span className="legal-sep">·</span>
            <span className="legal-roll">Roll No: M25AI2006</span>
            <span className="legal-sep">·</span>
            <span>Indian Institute of Technology Jodhpur</span>
            <span className="legal-sep">·</span>
            <span>
              {isUniverse ? "Historical SS calculations · independent JPL DE440 modern view" : isLearning || isResearch ? "SS calculations · separate saved DE440 comparison" : "Computed from the Surya Siddhanta (Burgess, 1860) — no external ephemeris"}
            </span>
          </footer>
        </main>
        {/* Outside <main>: the panel never reflows the page, and the page
            scan (which watches main.content) never sees the panel. */}
        <GlossaryPanel suppressed={chatOpen} openRequest={glossaryRequest} onShowChat={() => setChatOpen(true)} />
        <ChatPanel open={chatOpen} onClose={closeChat} onShowTerms={() => {
          setChatOpen(false);
          setGlossaryRequest(request => request + 1);
        }} />
      </div>
    </GlossaryProvider>
  );
}
