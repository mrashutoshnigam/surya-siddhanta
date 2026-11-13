import { useEffect, useRef, useState } from "react";

const STORAGE_KEY = "ss.project-introduction.dismissed";
const REPOSITORY = "https://github.com/mrashutoshnigam/surya-siddhanta";
const DOCUMENTS = `${REPOSITORY}/blob/main/docs`;
const RESOURCES = [
  { title: "GitHub repository", detail: "Source code & documentation", href: REPOSITORY },
  { title: "Project report", detail: "M.Tech. project report · PDF", href: `${DOCUMENTS}/Project_Report_Surya_Siddhanta_Computation_Library.pdf` },
  { title: "Computational edition paper", detail: "Running the Text · All fourteen chapters", href: `${DOCUMENTS}/paper/revision-wip/computational-edition/running-the-text-surya-siddhanta-computational-edition.pdf` },
  { title: "JPL DE440 comparison paper", detail: "Planetary accuracy · 1550–2649 CE", href: `${DOCUMENTS}/evaluation-de440/surya-siddhanta-vs-de440.pdf` },
  { title: "Python library (PyPI)", detail: "Install the surya-siddhanta package", href: "https://pypi.org/project/surya-siddhanta/" },
  { title: "Docker image (Docker Hub)", detail: "Run the application in a container", href: "https://hub.docker.com/r/mrashutoshnigam/surya-siddhanta" },
];

function wasDismissed() {
  try {
    return localStorage.getItem(STORAGE_KEY) === "1";
  } catch {
    return false;
  }
}

function IntroductionDialog({ onDismiss }: { onDismiss: () => void }) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    const dialog = ref.current;
    const previousOverflow = document.body.style.overflow;
    if (dialog && !dialog.open) dialog.showModal();
    titleRef.current?.focus({ preventScroll: true });
    document.body.style.overflow = "hidden";
    // Like TermDialog, unmount removes the top layer. Calling close during
    // StrictMode cleanup would queue a close event after the next setup.
    return () => { document.body.style.overflow = previousOverflow; };
  }, []);

  return (
    <dialog
      ref={ref}
      className="project-dialog"
      aria-labelledby="project-introduction-title"
      onClose={onDismiss}
      onKeyDown={event => {
        if (event.key !== "Tab") return;
        const controls = event.currentTarget.querySelectorAll<HTMLElement>("button, a[href]");
        const first = controls[0];
        const last = controls[controls.length - 1];
        if (event.shiftKey && (document.activeElement === first || document.activeElement === titleRef.current)) {
          event.preventDefault();
          last?.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first?.focus();
        }
      }}
      onClick={event => {
        if (event.target === event.currentTarget) ref.current?.close();
      }}
    >
      <div className="project-dialog-frame">
        <header className="project-dialog-header">
          <span>Surya Siddhanta <span aria-hidden="true">/</span> About the project</span>
          <button type="button" className="project-close" aria-label="Close project introduction" onClick={() => ref.current?.close()}>×</button>
        </header>
        <div className="project-dialog-body">
          <section className="project-title-page">
            <img className="project-institute-logo" src="/iit-jodhpur-logo.jpg" alt="IIT Jodhpur logo" width="82" height="90" />
            <h2 id="project-introduction-title" ref={titleRef} tabIndex={-1}>Computational Implementation of the Surya Siddhanta</h2>
            <p className="project-submission">A Project Submitted by</p>
            <p className="project-author">Ashutosh Nigam<span>M25AI2006</span></p>
            <p className="project-fulfillment">in partial fulfillment of the requirements<br className="project-desktop-break" /> for the award of the degree of</p>
            <p className="project-degree">M.Tech.</p>
            <div className="project-institute">
              <p>Indian Institute of Technology Jodhpur</p>
              <p>Department of Computer Science and Engineering</p>
            </div>
          </section>
          <aside className="project-resources" aria-labelledby="project-resources-title">
            <p className="project-eyebrow">Explore the work</p>
            <h3 id="project-resources-title">Code, research & resources</h3>
            <p className="project-resources-intro">Read the report and papers, explore the implementation, or install the Python library.</p>
            <ul>
              {RESOURCES.map(resource => (
                <li key={resource.title}>
                  <a href={resource.href} target="_blank" rel="noopener noreferrer">
                    <span><strong>{resource.title}</strong><small>{resource.detail}</small></span>
                    <span className="project-resource-arrow" aria-hidden="true">↗</span>
                    <span className="project-sr-only"> (opens in a new tab)</span>
                  </a>
                </li>
              ))}
            </ul>
          </aside>
        </div>
        <footer className="project-dialog-footer">
          <span>You can revisit this introduction from “About this project”.</span>
          <button className="project-explore" type="button" onClick={() => ref.current?.close()}>Explore the project <span aria-hidden="true">→</span></button>
        </footer>
      </div>
    </dialog>
  );
}

/** Auto-open on the first home-page visit; allow manual access on every page. */
export function ProjectWelcome({ isHome }: { isHome: boolean }) {
  const [dismissed, setDismissed] = useState(wasDismissed);
  const [manualOpen, setManualOpen] = useState(false);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const open = manualOpen || (isHome && !dismissed);

  function dismiss() {
    try {
      localStorage.setItem(STORAGE_KEY, "1");
    } catch {
      // Blocked storage still permits dismissing for this app session.
    }
    setDismissed(true);
    setManualOpen(false);
    requestAnimationFrame(() => triggerRef.current?.focus({ preventScroll: true }));
  }

  return (
    <>
      <button ref={triggerRef} className="project-about" type="button" onClick={() => setManualOpen(true)}>About this project</button>
      {open && <IntroductionDialog onDismiss={dismiss} />}
    </>
  );
}
