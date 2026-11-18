import { describe, expect, test } from "bun:test";
import { format, uuidV7 } from "../src/uuid/format.ts";
import { main, parseArgs } from "../src/cli.ts";

function capture(stdin = "") {
  const out: string[] = [];
  const err: string[] = [];
  const io = {
    out: (text: string) => out.push(text),
    err: (text: string) => err.push(text),
    readStdin: () => stdin,
  };
  return { io, out: () => out.join(""), err: () => err.join("") };
}

describe("parseArgs", () => {
  test("defaults the count to one", () => {
    expect(parseArgs(["gen"]).count).toBe(1);
  });

  test("reads -n and --count", () => {
    expect(parseArgs(["gen", "-n", "3"]).count).toBe(3);
    expect(parseArgs(["--count", "5", "gen"]).count).toBe(5);
  });

  test("rejects a bad count", () => {
    expect(() => parseArgs(["-n", "0"])).toThrow(/between 1 and 1000/);
    expect(() => parseArgs(["-n"])).toThrow(/needs a value/);
  });
});

describe("main", () => {
  test("gen prints one canonical v7 uuid", async () => {
    const c = capture();
    expect(await main(["gen"], c.io)).toBe(0);
    expect(c.out().trim()).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/);
  });

  test("gen --count prints that many distinct uuids", async () => {
    const c = capture();
    expect(await main(["gen", "--count", "5"], c.io)).toBe(0);
    const lines = c.out().trim().split("\n");
    expect(lines).toHaveLength(5);
    expect(new Set(lines).size).toBe(5);
  });

  test("parse prints the timestamp", async () => {
    const text = format(uuidV7(1_700_000_000_000, new Uint8Array(10)));
    const c = capture();
    expect(await main(["parse", text], c.io)).toBe(0);
    expect(c.out()).toContain("version=7");
    expect(c.out()).toContain("timestamp_ms=1700000000000");
    expect(c.out()).toContain("timestamp_iso=2023-11-14T22:13:20.000Z");
  });

  test("validate exits 1 on junk", async () => {
    const c = capture();
    expect(await main(["validate", "nope"], c.io)).toBe(1);
    expect(c.err()).toContain("not a uuid");
  });

  test("sort orders v7 uuids by generation time", async () => {
    const early = format(uuidV7(1_000, new Uint8Array(10)));
    const late = format(uuidV7(2_000, new Uint8Array(10)));
    const c = capture(`${late}\n${early}\n`);
    expect(await main(["sort"], c.io)).toBe(0);
    expect(c.out().trim().split("\n")).toEqual([early, late]);
  });

  test("sort refuses a line that is not a uuid", async () => {
    const c = capture("nope\n");
    expect(await main(["sort"], c.io)).toBe(1);
  });

  test("an unknown command exits 2", async () => {
    const c = capture();
    expect(await main(["frobnicate"], c.io)).toBe(2);
    expect(c.err()).toContain("unknown command");
  });

  test("no command exits 2", async () => {
    const c = capture();
    expect(await main([], c.io)).toBe(2);
  });

  test("--help exits 0", async () => {
    const c = capture();
    expect(await main(["--help"], c.io)).toBe(0);
    expect(c.out()).toContain("Usage:");
  });
});
