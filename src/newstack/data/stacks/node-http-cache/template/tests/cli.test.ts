import assert from "node:assert/strict";
import { test } from "node:test";
import { cli, parse, PROGRAM, UsageError } from "../src/cli.js";

async function quietly(work: () => Promise<number>): Promise<{ code: number; output: string }> {
  const lines: string[] = [];
  const log = console.log;
  const error = console.error;
  console.log = (...parts: unknown[]) => {
    lines.push(parts.map(String).join(" "));
  };
  console.error = (...parts: unknown[]) => {
    lines.push(parts.map(String).join(" "));
  };
  try {
    return { code: await work(), output: lines.join("\n") };
  } finally {
    console.log = log;
    console.error = error;
  }
}

test("--version names the program and exits 0", async () => {
  const result = await quietly(() => cli(["--version"]));
  assert.equal(result.code, 0);
  assert.match(result.output, new RegExp(`^${PROGRAM} 0\\.1\\.0$`));
});

test("help lists every command", async () => {
  const result = await quietly(() => cli(["help"]));
  assert.equal(result.code, 0);
  for (const word of ["demo", "check", "serve", "selftest"]) {
    assert.match(result.output, new RegExp(word));
  }
});

test("demo keeps every story", async () => {
  const result = await quietly(() => cli(["demo"]));
  assert.equal(result.code, 0, result.output);
  assert.equal((result.output.match(/kept        yes/g) ?? []).length, 6);
});

test("bad input exits 2", async () => {
  assert.equal((await quietly(() => cli(["--rounds", "0"]))).code, 2);
  assert.equal((await quietly(() => cli(["nope"]))).code, 2);
  assert.equal((await quietly(() => cli(["check"]))).code, 2);
  assert.throws(() => parse(["demo", "--port", "0"]), UsageError);
  assert.throws(() => parse(["demo", "--rounds"]), UsageError);
});
