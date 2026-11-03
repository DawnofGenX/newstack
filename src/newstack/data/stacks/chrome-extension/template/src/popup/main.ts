import {
  PING_MESSAGE,
  describePageState,
  isInspectable,
  stateFromProbe,
} from "../lib/activity";
import { COUNT_STORAGE_KEY, formatCount, nextCount, resetCount } from "../lib/counter";

const countEl = document.querySelector<HTMLParagraphElement>("#count");
const incrementBtn = document.querySelector<HTMLButtonElement>("#increment");
const resetBtn = document.querySelector<HTMLButtonElement>("#reset");
const statusEl = document.querySelector<HTMLParagraphElement>("#status");

let count = 0;
// A storage read is async: never let its callback clobber a click the user made first.
let userInteracted = false;

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
      if (typeof stored === "number" && !userInteracted) {
        count = Number.isFinite(stored) ? Math.max(0, Math.trunc(stored)) : 0;
        render();
      }
    });
  } catch {
    /* ignore */
  }
}

incrementBtn?.addEventListener("click", () => {
  userInteracted = true;
  count = nextCount(count);
  render();
  persist(count);
});

resetBtn?.addEventListener("click", () => {
  userInteracted = true;
  count = resetCount();
  render();
  persist(count);
});

/** Ask the tab's content script whether this extension is running there. */
function pingTab(tabId: number): Promise<boolean> {
  return new Promise((resolve) => {
    try {
      chrome.tabs.sendMessage(tabId, { type: PING_MESSAGE }, (reply) => {
        // A page loaded before the extension was installed has no receiver; that is
        // reported as "inactive", not as an error the user has to decipher.
        void chrome.runtime.lastError;
        resolve(Boolean((reply as { active?: boolean } | undefined)?.active));
      });
    } catch {
      resolve(false);
    }
  });
}

async function showPageState(): Promise<void> {
  if (!statusEl) return;
  if (typeof chrome === "undefined" || !chrome.tabs) {
    statusEl.textContent = describePageState("unsupported");
    return;
  }
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const inspectable = isInspectable(tab?.url);
    const responded =
      inspectable && typeof tab?.id === "number" ? await pingTab(tab.id) : false;
    statusEl.textContent = describePageState(stateFromProbe(responded, inspectable));
  } catch {
    statusEl.textContent = describePageState("unsupported");
  }
}

render();
restore();
void showPageState();
