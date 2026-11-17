import assert from "node:assert/strict";
import { test } from "node:test";

import { EventLog } from "../src/events.js";
import { Hub } from "../src/hub.js";

/// A response-shaped object that records what was written to it.
function fakeResponse() {
  return {
    chunks: [],
    writableEnded: false,
    destroyed: false,
    write(chunk) {
      this.chunks.push(chunk);
      return true;
    },
    get text() {
      return this.chunks.join("");
    },
  };
}

function hubWith(options) {
  const log = new EventLog();
  return { log, hub: new Hub(log, options) };
}

test("a fresh subscriber starts live and gets no history", () => {
  const { hub } = hubWith({});
  hub.publish("metrics", { n: 1 });
  const res = fakeResponse();
  hub.subscribe(res, { topic: "metrics" });
  assert.equal(res.text, "");
  assert.equal(hub.size, 1);
});

test("a subscriber that quotes an id is replayed from the log", () => {
  const { hub } = hubWith({});
  hub.publish("metrics", { n: 1 });
  hub.publish("metrics", { n: 2 });
  const res = fakeResponse();
  hub.subscribe(res, { topic: "metrics", lastId: "1" });
  assert.match(res.text, /id: 2/);
  assert.doesNotMatch(res.text, /id: 1/);
});

test("replay honours the topic filter", () => {
  const { hub } = hubWith({});
  hub.publish("metrics", { n: 1 });
  hub.publish("other", { n: 2 });
  const res = fakeResponse();
  hub.subscribe(res, { topic: "metrics", lastId: 0 });
  assert.match(res.text, /id: 1/);
  assert.doesNotMatch(res.text, /id: 2/);
});

test("publish delivers only to matching subscribers", () => {
  const { hub } = hubWith({});
  const metrics = fakeResponse();
  const other = fakeResponse();
  const everything = fakeResponse();
  hub.subscribe(metrics, { topic: "metrics" });
  hub.subscribe(other, { topic: "other" });
  hub.subscribe(everything, {});

  hub.publish("metrics", { n: 1 });

  assert.match(metrics.text, /event: metrics/);
  assert.equal(other.text, "");
  assert.match(everything.text, /event: metrics/);
});

test("a dead subscriber is pruned on the next write instead of throwing", () => {
  const { hub } = hubWith({});
  const gone = fakeResponse();
  const alive = fakeResponse();
  hub.subscribe(gone, {});
  hub.subscribe(alive, {});
  gone.writableEnded = true;

  hub.publish("metrics", { n: 1 });

  assert.equal(hub.size, 1);
  assert.match(alive.text, /id: 1/);
});

test("remove() is what the close listener calls", () => {
  const { hub } = hubWith({});
  const res = fakeResponse();
  hub.subscribe(res, {});
  hub.remove(res);
  assert.equal(hub.size, 0);
});

test("the heartbeat writes comments to every live subscriber", async () => {
  const { hub } = hubWith({ heartbeatMs: 20 });
  const res = fakeResponse();
  hub.subscribe(res, {});
  await new Promise((r) => setTimeout(r, 80));
  hub.close();
  assert.match(res.text, /: ping/);
  assert.doesNotMatch(res.text, /id: /);
});

test("a heartbeat interval of zero means no timer at all", async () => {
  const { hub } = hubWith({ heartbeatMs: 0 });
  const res = fakeResponse();
  hub.subscribe(res, {});
  await new Promise((r) => setTimeout(r, 50));
  hub.close();
  assert.equal(res.text, "");
});
