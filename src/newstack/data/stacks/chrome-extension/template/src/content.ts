/**
 * Content script: marks the page so you can eyeball that injection worked.
 * Guarded so importing this file outside a page context is harmless.
 */

import { PING_MESSAGE, PING_REPLY } from "./lib/activity";

export const MARKER_ATTRIBUTE = "data-newstack-extension";

export function markDocument(doc: Document | undefined): boolean {
  if (!doc || !doc.body) return false;
  doc.body.setAttribute(MARKER_ATTRIBUTE, "on");
  return true;
}

if (typeof document !== "undefined") {
  if (document.body) {
    markDocument(document);
  } else {
    document.addEventListener("DOMContentLoaded", () => markDocument(document), { once: true });
  }
}

// The popup asks "are you there?" so it can state the page state instead of guessing.
if (typeof chrome !== "undefined" && chrome.runtime?.onMessage) {
  chrome.runtime.onMessage.addListener((message: unknown, _sender, sendResponse) => {
    const type = (message as { type?: string } | null)?.type;
    if (type === PING_MESSAGE) {
      sendResponse(PING_REPLY);
    }
    return false;
  });
}
