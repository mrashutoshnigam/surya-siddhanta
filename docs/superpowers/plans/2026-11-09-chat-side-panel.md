# Chat Side Panel Implementation Plan

**Goal:** Apply the approved chat-panel proposal without committing changes.

**Architecture:** Keep the existing chat mounted in the shared Layout. The sidebar toggles a right-hand panel; chat and glossary share that space. A native modal dialog provides the full-screen mobile variant; desktop remains non-modal, docking only when enough space exists. Existing /chat bookmarks redirect to Planet Positions with the panel open.

**Tech stack:** Existing React, React Router, CSS tokens, native dialog, Playwright.

**Constraints:** No commits, no new dependencies, no backend changes. Conversation and draft persist during navigation, closing, and glossary switching for the lifetime of the app session; browser reload persistence is outside scope. Preserve location, citations, Markdown, calculation traces, themes, and reduced motion.

## Implementation

- [x] Add a browser check covering sidebar opening without navigation, send/session continuity, draft preservation, citations, request failure/retry, glossary switching, legacy /chat entry, mobile focus/Escape/overflow, and desktop docking.
- [x] Run the check before implementation and confirm it fails because the sidebar still navigates to a page.
- [x] Add ChatPanel, reuse Chat content, coordinate glossary visibility, replace the navigation link with a button, and redirect /chat bookmarks.
- [x] Scope layout/styles to the panel and preserve the application design tokens.
- [x] Run build, chat-panel browser checks, existing project-introduction checks, strict UI audit, and diff whitespace checks. Inspect mobile and desktop screenshots.
- [x] Document the canonical panel behavior in DESIGN.md and leave all changes uncommitted.

## Verification record

The initial browser check failed because the sidebar AI entry was still a page link. The completed chat check passes for route/draft/session continuity, pending responses while hidden, citations, retry, IME and duplicate-submit guards, glossary switching, mobile modal/focus/Escape, desktop docking, themes, long Markdown/tool output, reset and fresh legacy /chat links. The existing project-introduction check passes on 39 routes. Build and strict static audit pass. Screenshots were inspected in light/dark and mobile. Independent review found no important actionable issues. The fresh legacy-link test explicitly waits for native dialog effect cleanup before asserting scroll restoration. No commits were created.

## Review focus

Requests finishing while chat is hidden must remain in the same conversation. Duplicate sends and IME Enter must not submit twice. Failed requests must be recoverable without losing the question. Mobile modal focus and scroll lock must survive resize; desktop must remain interactive. Chat must never cover an active glossary, and citation navigation must preserve the chat session.
