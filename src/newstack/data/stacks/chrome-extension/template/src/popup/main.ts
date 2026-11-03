import { COUNT_STORAGE_KEY, formatCount, nextCount, resetCount } from "../lib/counter";

const countEl = document.querySelector<HTMLParagraphElement>("#count");
const incrementBtn = document.querySelector<HTMLButtonElement>("#increment");
const resetBtn = document.querySelector<HTMLButtonElement>("#reset");

let count = 0;

function render(): void {
  if (countEl) countEl.textContent = formatCount(count);
}

function persist(value: number): void {
  // chrome.storage is unavailable outside an extension host (e.g. plain vite dev).
  if (typeof chrome === "undefined" || !chrome.storage?.local) return;
  try {
    void chrome.storage.local.set({ [COUNT_STORAGE_KEY]: value });
  } catch {
    /* storage is best effort; the popup still works without it */
  }
}

function restore(): void {
  if (typeof chrome === "undefined" || !chrome.storage?.local) return;
  try {
    chrome.storage.local.get(COUNT_STORAGE_KEY, (items) => {
      const stored = items?.[COUNT_STORAGE_KEY];
      if (typeof stored === "number") {
        count = Number.isFinite(stored) ? Math.max(0, Math.trunc(stored)) : 0;
        render();
      }
    });
  } catch {
    /* ignore */
  }
}

incrementBtn?.addEventListener("click", () => {
  count = nextCount(count);
  render();
  persist(count);
});

resetBtn?.addEventListener("click", () => {
  count = resetCount();
  render();
  persist(count);
});

render();
restore();
