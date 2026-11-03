/**
 * "Is this extension active on the tab the popup is showing?"
 *
 * The content script answers a ping. Everything that decides what to *say* is pure, so
 * the messaging layer stays thin and can be tested without a browser.
 */

export const PING_MESSAGE = "newstack:ping";
export const PING_REPLY = { active: true } as const;

export type PageState = "active" | "inactive" | "unsupported";

/** Pages an extension can never reach, so there is nothing to report but the truth. */
export function isInspectable(url: string | undefined | null): boolean {
  if (!url) return false;
  return /^(https?|file):/i.test(url);
}

/** Combine "were we allowed to ask?" with "did anything answer?". */
export function stateFromProbe(responded: boolean, inspectable: boolean): PageState {
  if (!inspectable) return "unsupported";
  return responded ? "active" : "inactive";
}

export function describePageState(state: PageState): string {
  switch (state) {
    case "active":
      return "Active on this page";
    case "inactive":
      return "Not active on this page \u2014 reload the tab to inject the content script";
    default:
      return "Can\u0027t run on this page (browser pages are off limits)";
  }
}
