import assert from "node:assert/strict";
import test from "node:test";

import { EXIT_OK, EXIT_UNUSABLE, PROGRAM, VERSION, run } from "../src/main.js";

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

test("the banner names the program", async () => {
  assert.equal(await quietly(() => run(["--version"])), EXIT_OK);
  assert.ok(PROGRAM.length > 0);
  assert.equal(VERSION, "0.1.0");
});

test("no arguments prints usage", async () => {
  assert.equal(await quietly(() => run([])), EXIT_OK);
});

test("bench keeps the pool contract", async () => {
  assert.equal(await quietly(() => run(["bench", "--size", "2", "--tasks", "8"])), EXIT_OK);
});

test("bench refuses a zero size", async () => {
  assert.equal(await quietly(() => run(["bench", "--size", "0"])), EXIT_UNUSABLE);
});

test("bench refuses a non-integer", async () => {
  assert.equal(await quietly(() => run(["bench", "--tasks", "many"])), EXIT_UNUSABLE);
});

test("an option without a value is unusable", async () => {
  assert.equal(await quietly(() => run(["bench", "--tasks"])), EXIT_UNUSABLE);
});

test("an unknown command is unusable", async () => {
  assert.equal(await quietly(() => run(["nope"])), EXIT_UNUSABLE);
});

test("demo runs every story", async () => {
  assert.equal(await quietly(() => run(["demo"])), EXIT_OK);
});
