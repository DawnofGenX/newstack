import assert from "node:assert/strict";
import test from "node:test";

import { countText } from "../src/counts.js";
import { handleFrame } from "../src/protocol.js";

test("counts lines, words and bytes the way wc does", () => {
  assert.deepEqual(countText(""), { lines: 0, words: 0, bytes: 0 });
  assert.deepEqual(countText("hello world\n"), { lines: 1, words: 2, bytes: 12 });
  assert.deepEqual(countText("a b\nc\n"), { lines: 2, words: 3, bytes: 6 });
  assert.deepEqual(countText("h\u00e9llo w\u00f6rld\n"), { lines: 1, words: 2, bytes: 14 });
  assert.deepEqual(countText("lone\u000bvertical"), { lines: 0, words: 2, bytes: 13 });
});

test("a stats frame is answered with counts and no echo of the text", () => {
  const outcome = handleFrame(JSON.stringify({ type: "stats", text: "a b\nc\n" }));
  assert.equal(outcome.kind, "reply");
  assert.deepEqual(outcome.frame, { type: "stats", lines: 2, words: 3, bytes: 6 });
});

test("broken JSON and unknown types are reported, not fatal", () => {
  const broken = handleFrame("{");
  assert.equal(broken.kind, "error");
  assert.equal(broken.frame.code, "invalid_json");

  const unknown = handleFrame(JSON.stringify({ type: "shout" }));
  assert.equal(unknown.kind, "error");
  assert.equal(unknown.frame.code, "unknown_type");

  const notObject = handleFrame(JSON.stringify([1, 2]));
  assert.equal(notObject.frame.code, "invalid_json");
});

test("a stats frame without a string text is invalid_text", () => {
  const outcome = handleFrame(JSON.stringify({ type: "stats", text: 42 }));
  assert.equal(outcome.kind, "error");
  assert.equal(outcome.frame.code, "invalid_text");
});

test("ping is answered with a pong", () => {
  assert.deepEqual(handleFrame(JSON.stringify({ type: "ping" })).frame, { type: "pong" });
});
