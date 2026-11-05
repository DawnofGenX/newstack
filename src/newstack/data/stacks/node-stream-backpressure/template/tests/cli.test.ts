import assert from "node:assert/strict";
import test from "node:test";

import { EXIT_OK, EXIT_STALLED, EXIT_UNUSABLE, PROGRAM, VERSION, run } from "../src/main.js";

// console only: the test reporter writes to process.stdout itself, and an async
// write issued while that method is stubbed never reaches the terminal.
async function quietly(fn: () => Promise<number>): Promise<number> {
  const error = console.error;
  const log = console.log;
  console.error = () => undefined;
  console.log = () => undefined;
  try {
    return await fn();
  } finally {
    console.error = error;
    console.log = log;
  }
}

test("the banner carries a program name", async () => {
  assert.equal(await quietly(() => run(["--version"])), EXIT_OK);
  assert.ok(PROGRAM.length > 0, "the program name is empty");
  assert.equal(VERSION, "0.1.0");
});

test("no arguments prints usage and succeeds", async () => {
  assert.equal(await quietly(() => run([])), EXIT_OK);
});

test("compare passes when the bounded mode holds", async () => {
  assert.equal(await quietly(() => run(["compare", "--chunks", "24"])), EXIT_OK);
});

test("compare fails when the bound is impossible", async () => {
  const code = await quietly(() =>
    run(["compare", "--chunks", "24", "--max-peak-chunks", "0"]),
  );
  assert.equal(code, EXIT_STALLED);
});

test("compare refuses zero chunks", async () => {
  assert.equal(await quietly(() => run(["compare", "--chunks", "0"])), EXIT_UNUSABLE);
});

test("compare refuses a non-integer", async () => {
  assert.equal(await quietly(() => run(["compare", "--chunks", "many"])), EXIT_UNUSABLE);
});

test("an option without a value is unusable, not a crash", async () => {
  assert.equal(await quietly(() => run(["compare", "--chunks"])), EXIT_UNUSABLE);
});

test("an unknown command is unusable", async () => {
  assert.equal(await quietly(() => run(["nope"])), EXIT_UNUSABLE);
});

test("demo runs the whole story list", async () => {
  assert.equal(await quietly(() => run(["demo"])), EXIT_OK);
});
