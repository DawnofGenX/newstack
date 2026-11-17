import assert from "node:assert/strict";
import { test } from "node:test";

import { HEARTBEAT, assertTopic, frame } from "../src/frame.js";

test("a frame is id, event, data and a blank line", () => {
  assert.equal(
    frame({ id: 7, topic: "metrics", data: { n: 1 } }),
    'id: 7\nevent: metrics\ndata: {"n":1}\n\n',
  );
});

test("a multi-line payload stays one event because it is JSON", () => {
  const text = frame({ id: 1, topic: "log", data: "one\ntwo" });
  assert.equal(text.split("\n\n").length, 2);
  assert.match(text, /data: "one\\ntwo"/);
});

test("a null payload is still a data line", () => {
  assert.equal(frame({ id: 1, topic: "tick", data: null }), "id: 1\nevent: tick\ndata: null\n\n");
});

test("a topic that would inject a frame is refused", () => {
  for (const bad of ["bad topic", "a\nb", "", " ", "-leading", "a:b", null, 7]) {
    assert.throws(() => assertTopic(bad), RangeError, `expected ${JSON.stringify(bad)} to be refused`);
  }
});

test("ordinary topic names are accepted", () => {
  for (const good of ["metrics", "a.b", "A_1-2", "x"]) {
    assert.equal(assertTopic(good), good);
  }
});

test("the heartbeat is a comment, so clients do not see it as an event", () => {
  assert.equal(HEARTBEAT, ": ping\n\n");
  assert.ok(HEARTBEAT.startsWith(":"));
});
