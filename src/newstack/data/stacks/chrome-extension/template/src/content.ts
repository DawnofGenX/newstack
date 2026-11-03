/**
 * Content script: marks the page so you can eyeball that injection worked.
 * Guarded so importing this file outside a page context is harmless.
 */

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
