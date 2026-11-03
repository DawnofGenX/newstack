import { describe, expect, it } from "bun:test";
import { parseArgs } from "../src/textstat/options.ts";

describe("options", () => {
  it("no arguments means every figure and standard input", () => {
    expect(parseArgs([])).toEqual({
      ok: true,
      options: { mode: "all", help: false, version: false, files: [] },
    });
  });

  it("each mode flag is accepted long and short", () => {
    const flags: Array<[string, string]> = [
      ["-l", "lines"],
      ["--lines", "lines"],
      ["-w", "words"],
      ["--words", "words"],
      ["-c", "bytes"],
      ["--bytes", "bytes"],
    ];
    for (const [flag, mode] of flags) {
      const parsed = parseArgs([flag]);
      expect(parsed.ok).toBe(true);
      if (parsed.ok) expect(parsed.options.mode).toBe(mode);
    }
  });

  it("-l selects lines and keeps the file", () => {
    const parsed = parseArgs(["-l", "a.txt"]);
    expect(parsed.ok).toBe(true);
    if (parsed.ok) {
      expect(parsed.options.mode).toBe("lines");
      expect(parsed.options.files).toEqual(["a.txt"]);
    }
  });

  it("repeating the same mode is allowed", () => {
    expect(parseArgs(["-l", "--lines"]).ok).toBe(true);
    expect(parseArgs(["-c", "--bytes"]).ok).toBe(true);
  });

  it("conflicting modes are a usage error", () => {
    const parsed = parseArgs(["-l", "-c"]);
    expect(parsed.ok).toBe(false);
    if (!parsed.ok) expect(parsed.reason).toContain("conflicts");
  });

  it("--help stops parsing", () => {
    const parsed = parseArgs(["--help", "-l"]);
    expect(parsed.ok).toBe(true);
    if (parsed.ok) expect(parsed.options.help).toBe(true);
  });

  it("-h is the short form of --help", () => {
    const parsed = parseArgs(["-h"]);
    expect(parsed.ok).toBe(true);
    if (parsed.ok) expect(parsed.options.help).toBe(true);
  });

  it("-V is a separate outcome from --help", () => {
    const parsed = parseArgs(["-V"]);
    expect(parsed.ok).toBe(true);
    if (parsed.ok) {
      expect(parsed.options.version).toBe(true);
      expect(parsed.options.help).toBe(false);
    }
  });

  it("an unknown flag is a usage error", () => {
    expect(parseArgs(["--bogus"])).toEqual({
      ok: false,
      reason: "unknown option '--bogus'",
    });
  });

  it("collects multiple files", () => {
    const parsed = parseArgs(["a.txt", "b.txt"]);
    expect(parsed.ok).toBe(true);
    if (parsed.ok) expect(parsed.options.files).toEqual(["a.txt", "b.txt"]);
  });

  it("-- ends option parsing", () => {
    const parsed = parseArgs(["--", "-l"]);
    expect(parsed.ok).toBe(true);
    if (parsed.ok) {
      expect(parsed.options.files).toEqual(["-l"]);
      expect(parsed.options.mode).toBe("all");
    }
  });

  it("a bare - is a file (standard input)", () => {
    const parsed = parseArgs(["-"]);
    expect(parsed.ok).toBe(true);
    if (parsed.ok) expect(parsed.options.files).toEqual(["-"]);
  });

  it("an empty string is a file, not an option", () => {
    const parsed = parseArgs([""]);
    expect(parsed.ok).toBe(true);
    if (parsed.ok) expect(parsed.options.files).toEqual([""]);
  });
});
