import assert from "node:assert/strict";
import { test } from "node:test";

import { EventLog } from "../src/events.js";

test("ids start at 1 and only ever go up", () => {
  const log = new EventLog();
  assert.equal(log.lastId, 0);
  assert.equal(log.append("a", 1).id, 1);
  assert.equal(log.append("a", 2).id, 2);
  assert.equal(log.lastId, 2);
});

test("the log is bounded and drops the oldest events first", () => {
  const log = new EventLog({ limit: 3 });
  for (const n of [1, 2, 3, 4, 5]) log.append("a", n);
  assert.equal(log.size, 3);
  assert.deepEqual(
    log.since(0).map((event) => event.data),
    [3, 4, 5],
  );
});

test("since() is strictly greater-than, which is what Last-Event-ID means", () => {
  const log = new EventLog();
  log.append("a", "one");
  log.append("a", "two");
  log.append("a", "three");
  assert.deepEqual(
    log.since(2).map((event) => event.data),
    ["three"],
  );
  assert.deepEqual(
    log.since(1).map((event) => event.data),
    ["two", "three"],
  );
});

test("since() past the end is empty, since() before the window starts gives the window", () => {
  const log = new EventLog({ limit: 2 });
  log.append("a", 1);
  log.append("a", 2);
  log.append("a", 3);
  assert.deepEqual(log.since(3), []);
  assert.deepEqual(
    log.since(0).map((event) => event.data),
    [2, 3],
  );
});

test("an unusable id replays the whole retained window instead of throwing", () => {
  const log = new EventLog();
  log.append("a", 1);
  assert.equal(log.since("not-a-number").length, 1);
});

test("a zero or negative limit is refused", () => {
  assert.throws(() => new EventLog({ limit: 0 }), RangeError);
  assert.throws(() => new EventLog({ limit: 1.5 }), RangeError);
});
