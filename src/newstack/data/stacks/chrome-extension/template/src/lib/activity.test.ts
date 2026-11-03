import { describe, expect, it } from "vitest";

import { describePageState, isInspectable, stateFromProbe } from "./activity";

describe("isInspectable", () => {
  it("accepts pages a content script can reach", () => {
    expect(isInspectable("https://example.com")).toBe(true);
    expect(isInspectable("http://localhost:3000/app")).toBe(true);
    expect(isInspectable("file:///home/me/page.html")).toBe(true);
  });

  it("rejects browser-internal and unknown pages", () => {
    expect(isInspectable("chrome://extensions")).toBe(false);
    expect(isInspectable("edge://settings")).toBe(false);
    expect(isInspectable("about:blank")).toBe(false);
    expect(isInspectable(undefined)).toBe(false);
    expect(isInspectable("")).toBe(false);
  });
});

describe("stateFromProbe", () => {
  it("reports active only when the content script answered", () => {
    expect(stateFromProbe(true, true)).toBe("active");
    expect(stateFromProbe(false, true)).toBe("inactive");
  });

  it("never claims a page state it could not check", () => {
    expect(stateFromProbe(true, false)).toBe("unsupported");
    expect(stateFromProbe(false, false)).toBe("unsupported");
  });
});

describe("describePageState", () => {
  it("tells the user what to do about an inactive tab", () => {
    expect(describePageState("active")).toBe("Active on this page");
    expect(describePageState("inactive")).toContain("reload");
    expect(describePageState("unsupported")).toContain("off limits");
  });
});
