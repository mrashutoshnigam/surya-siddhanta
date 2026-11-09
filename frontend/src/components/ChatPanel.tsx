import { useEffect, useRef, useState } from "react";
import { Chat } from "../pages/Chat";

/** One persistent conversation; desktop is non-modal, phones use a modal drawer. */
export function ChatPanel({ open, onClose, onShowTerms }: {
  open: boolean;
  onClose: () => void;
  onShowTerms: () => void;
}) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const headingRef = useRef<HTMLHeadingElement>(null);
  const [mobile, setMobile] = useState(() => window.matchMedia("(max-width: 767px)").matches);

  useEffect(() => {
    const query = window.matchMedia("(max-width: 767px)");
    const update = () => setMobile(query.matches);
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, []);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (dialog.open) dialog.close();
    if (!open) return;
    const previousOverflow = document.body.style.overflow;
    if (mobile) {
      dialog.showModal();
      document.body.style.overflow = "hidden";
    } else {
      dialog.show();
    }
    headingRef.current?.focus({ preventScroll: true });
    const conversation = dialog.querySelector<HTMLElement>(".chat-window");
    if (conversation) conversation.scrollTop = conversation.scrollHeight;
    return () => {
      if (mobile) document.body.style.overflow = previousOverflow;
      dialog.close();
    };
  }, [open, mobile]);

  return (
    <dialog
      ref={dialogRef}
      id="chat-panel"
      className="chat-panel"
      aria-labelledby="chat-panel-title"
      onCancel={event => { event.preventDefault(); onClose(); }}
      onKeyDown={event => {
        if (event.key === "Escape" && !event.nativeEvent.isComposing) {
          event.preventDefault();
          onClose();
        } else if (mobile && event.key === "Tab") {
          const controls = Array.from(event.currentTarget.querySelectorAll<HTMLElement>(
            "button:not(:disabled), a[href], input:not(:disabled), textarea:not(:disabled), summary",
          )).filter(element => element.getClientRects().length > 0);
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
        <button type="button" className="chat-panel-terms" onClick={onShowTerms}>Terms</button>
        <button type="button" className="glossary-close" aria-label="Close chat" onClick={onClose}>×</button>
      </header>
      <Chat />
    </dialog>
  );
}
