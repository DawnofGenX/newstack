/**
 * MV3 service worker.
 *
 * Every chrome.* access is guarded so this module can still be imported in a
 * plain Node/Vitest environment without throwing.
 */

export const INSTALLED_KEY = "installedAt";

export interface InstallDetails {
  reason: string;
}

/** Seed storage on first install. Safe to call with no chrome runtime. */
export function handleInstalled(details: InstallDetails): void {
  if (details.reason !== "install") return;
  if (typeof chrome === "undefined" || !chrome.storage?.local) return;
  try {
    void chrome.storage.local.set({
      [INSTALLED_KEY]: Date.now(),
      count: 0,
    });
    console.info("[extension] installed and storage initialised");
  } catch (error) {
    console.warn("[extension] could not initialise storage", error);
  }
}

if (typeof chrome !== "undefined" && chrome.runtime?.onInstalled) {
  chrome.runtime.onInstalled.addListener((details) => {
    handleInstalled({ reason: details.reason });
  });
}
