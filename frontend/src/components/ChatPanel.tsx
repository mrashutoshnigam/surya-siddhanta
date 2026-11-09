import { useEffect, useRef, useState } from "react";
import { Chat } from "../pages/Chat";
import { GlossaryPanel } from "../glossary/GlossaryPanel";

export type PanelTab = "chat" | "terms";

function ChatIcon() {
  return <svg aria-hidden="true" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20 11.5a8 8 0 0 1-8 8H5l-4 3v-11a8 8 0 0 1 8-8h3a8 8 0 0 1 8 8Z" transform="translate(1 -1)" />
    <path d="M7 9h9M7 13h6" />
  </svg>;
}

/** One persistent conversation; desktop is non-modal, phones use a modal drawer. */
export function ChatPanel({ open, tab, onClose, onOpen, onTabChange }: {
  open: boolean;
  tab: PanelTab;
  onClose: () => void;
  onOpen: (trigger: HTMLButtonElement) => void;
  onTabChange: (tab: PanelTab) => void;
}) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const headingRef = useRef<HTMLHeadingElement>(null);
  const [mobile, setMobile] = useState(() => window.matchMedia("(max-width: 767px)").matches);
  const [presentation, setPresentation] = useState(0);

  useEffect(() => {
    if (!open || tab !== "chat") return;
    const conversation = dialogRef.current?.querySelector<HTMLElement>(".chat-window");
    if (conversation) conversation.scrollTop = conversation.scrollHeight;
  }, [open, tab]);

  useEffect(() => {
    const query = window.matchMedia("(max-width: 767px)");
    const update = () => setMobile(query.matches);
    update();
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, []);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (!open) {
      if (dialog.open) dialog.close();
      return;
    }
    // Reopening a parent would push it above an existing definition modal.
    // Defer the mode change until that topmost dialog has finished closing.
    const definition = dialog.querySelector<HTMLDialogElement>("dialog[open]");
    if (definition) {
      const resume = () => setPresentation(value => value + 1);
      definition.addEventListener("close", resume, { once: true });
      return () => definition.removeEventListener("close", resume);
    }
    if (dialog.open && dialog.matches(":modal") === mobile) return;
    if (dialog.open) dialog.close();
    if (mobile) dialog.showModal(); else dialog.show();
    headingRef.current?.focus({ preventScroll: true });
    const conversation = dialog.querySelector<HTMLElement>(".chat-window");
    if (conversation) conversation.scrollTop = conversation.scrollHeight;
  }, [open, mobile, presentation]);

  useEffect(() => {
    if (!open || !mobile) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => { document.body.style.overflow = previousOverflow; };
  }, [open, mobile]);

  useEffect(() => {
    const dialog = dialogRef.current;
    return () => dialog?.close();
  }, []);

  return (
    <>
    <button
      type="button"
      className="assistant-launcher"
      hidden={open}
      aria-label="Open AI Chat and Terms"
      title="Open AI Chat and Terms"
      aria-expanded={false}
      aria-controls="chat-panel"
      onClick={event => onOpen(event.currentTarget)}
    ><ChatIcon /></button>
    <dialog
      ref={dialogRef}
      id="chat-panel"
      className="chat-panel"
      aria-labelledby="chat-panel-title"
      onCancel={event => {
        if (event.target !== event.currentTarget) return;
        event.preventDefault();
        onClose();
      }}
      onKeyDown={event => {
        if (event.target instanceof Element && event.target.closest("dialog") !== event.currentTarget) return;
        if (event.key === "Escape" && !event.nativeEvent.isComposing) {
          event.preventDefault();
          onClose();
        } else if (mobile && event.key === "Tab") {
          const controls = Array.from(event.currentTarget.querySelectorAll<HTMLElement>(
            "button:not(:disabled), a[href], input:not(:disabled), textarea:not(:disabled), summary",
          )).filter(element => element.tabIndex >= 0 && element.getClientRects().length > 0);
          const first = controls[0];
          const last = controls[controls.length - 1];
          if (event.shiftKey && (document.activeElement === first || document.activeElement === headingRef.current)) {
            event.preventDefault();
            last?.focus();
          } else if (!event.shiftKey && document.activeElement === last) {
            event.preventDefault();
            first?.focus();
          }
        }
      }}
    >
      <header className="chat-panel-header">
        <h2 id="chat-panel-title" ref={headingRef} tabIndex={-1}>Surya Siddhanta AI</h2>
        <button type="button" className="glossary-close" aria-label="Close panel" onClick={onClose}>×</button>
      </header>
      <div className="side-panel-tabs" role="tablist" aria-label="Side panel" onKeyDown={event => {
        const keys = ["ArrowLeft", "ArrowRight", "Home", "End"];
        if (!keys.includes(event.key)) return;
        event.preventDefault();
        const next = event.key === "Home" ? "chat" : event.key === "End" ? "terms" : tab === "chat" ? "terms" : "chat";
        onTabChange(next);
        event.currentTarget.querySelector<HTMLButtonElement>(`#side-panel-${next}-tab`)?.focus();
      }}>
        <button id="side-panel-chat-tab" type="button" role="tab" aria-selected={tab === "chat"} aria-controls="side-panel-chat" tabIndex={tab === "chat" ? 0 : -1} onClick={() => onTabChange("chat")}><ChatIcon /><span>AI Chat</span></button>
        <button id="side-panel-terms-tab" type="button" role="tab" aria-selected={tab === "terms"} aria-controls="side-panel-terms" tabIndex={tab === "terms" ? 0 : -1} onClick={() => onTabChange("terms")}>Terms</button>
      </div>
      <div className="side-panel-view" id="side-panel-chat" role="tabpanel" aria-labelledby="side-panel-chat-tab" hidden={tab !== "chat"}><Chat /></div>
      <div className="side-panel-view" id="side-panel-terms" role="tabpanel" aria-labelledby="side-panel-terms-tab" hidden={tab !== "terms"}><GlossaryPanel active={open && tab === "terms"} /></div>
    </dialog>
    </>
  );
}
