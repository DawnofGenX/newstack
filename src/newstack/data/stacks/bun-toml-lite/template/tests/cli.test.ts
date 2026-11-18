import { describe, expect, test } from "bun:test";
import { main } from "../src/cli.ts";

function capture(argv: string[], stdin = "") {
  const out: string[] = [];
  const err: string[] = [];
  return main(argv, {
    out: (text) => out.push(text),
    err: (text) => err.push(text),
    readStdin: () => stdin,
  }).then((status) => ({ status, out: out.join(""), err: err.join("") }));
}

describe("cli", () => {
  test("prints JSON for stdin", async () => {
    const result = await capture([], 'a = 1\n[b]\nc = "two"\n');
    expect(result.status).toBe(0);
    expect(JSON.parse(result.out)).toEqual({ a: 1, b: { c: "two" } });
  });

  test("--get prints a single scalar", async () => {
    const result = await capture(["--get", "server.host"], '[server]\nhost = "localhost"\n');
    expect(result.status).toBe(0);
    expect(result.out).toBe("localhost\n");
  });

  test("--flatten prints dotted keys", async () => {
    const result = await capture(["--flatten"], '[db]\nport = 5432\nhost = "db"\n');
    expect(result.status).toBe(0);
    expect(result.out.trim().split("\n").sort()).toEqual(["db.host=db", "db.port=5432"]);
  });

  test("--help exits 0", async () => {
    const result = await capture(["--help"]);
    expect(result.status).toBe(0);
    expect(result.out).toContain("--flatten");
  });

  test("an unknown option exits 2", async () => {
    const result = await capture(["--bogus"]);
    expect(result.status).toBe(2);
    expect(result.err).toContain("unknown option");
  });

  test("--get without a key exits 2", async () => {
    const result = await capture(["--get"], "a = 1\n");
    expect(result.status).toBe(2);
  });

  test("a missing key exits 1", async () => {
    const result = await capture(["--get", "nope"], "a = 1\n");
    expect(result.status).toBe(1);
    expect(result.err).toContain("no such key");
  });

  test("a syntax error exits 1 and names the line", async () => {
    const result = await capture([], "a = \n");
    expect(result.status).toBe(1);
    expect(result.err).toContain("line 1:");
  });

  test("an unreadable file exits 1", async () => {
    const result = await capture(["does-not-exist.toml"]);
    expect(result.status).toBe(1);
    expect(result.err).toContain("cannot read");
  });
});
