#!/usr/bin/env node
// A contract against a *running* server: the parts a unit test cannot see,
// because they only exist over a real socket.
//
//   node tools/contract.mjs --base http://127.0.0.1:5469
//   node tools/contract.mjs --base ... --expect-heartbeat
//
// Exits non-zero on the first broken promise, with the frame that broke it.

import process from "node:process";

const args = process.argv.slice(2);
let base = "http://127.0.0.1:5469";
for (let i = 0; i < args.length; i += 1) {
  if (args[i] === "--base") base = args[i + 1];
}
const expectHeartbeat = args.includes("--expect-heartbeat");

let checks = 0;
function ok(label) {
  checks += 1;
  console.log(`  ok   ${label}`);
}
function fail(label, detail) {
  console.error(`  FAIL ${label}${detail ? `: ${detail}` : ""}`);
  process.exit(1);
}
function assert(condition, label, detail) {
  if (condition) ok(label);
  else fail(label, detail);
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function withTimeout(promise, ms, what) {
  let timer;
  try {
    return await Promise.race([
      promise,
      new Promise((_, reject) => {
        timer = setTimeout(() => reject(new Error(`timed out after ${ms}ms waiting for ${what}`)), ms);
      }),
    ]);
  } finally {
    clearTimeout(timer);
  }
}

/// Reads one SSE stream as frames, keeping the leftovers between calls.
class Stream {
  constructor(response) {
    this.response = response;
    this.reader = response.body.getReader();
    this.decoder = new TextDecoder();
    this.buffer = "";
    this.closed = false;
  }

  static async open(url, headers = {}) {
    const controller = new AbortController();
    const response = await fetch(url, { headers, signal: controller.signal });
    if (!response.ok) throw new Error(`${url} answered ${response.status}`);
    const stream = new Stream(response);
    stream.controller = controller;
    return stream;
  }

  async next(ms = 5000) {
    const deadline = Date.now() + ms;
    for (;;) {
      const boundary = this.buffer.indexOf("\n\n");
      if (boundary !== -1) {
        const block = this.buffer.slice(0, boundary);
        this.buffer = this.buffer.slice(boundary + 2);
        return Stream.parse(block);
      }
      const remaining = deadline - Date.now();
      if (remaining <= 0) throw new Error(`no frame within ${ms}ms (buffer=${JSON.stringify(this.buffer)})`);
      const read = await withTimeout(this.reader.read(), remaining, "the next chunk");
      if (read.done) {
        this.closed = true;
        throw new Error(`stream ended while waiting for a frame (buffer=${JSON.stringify(this.buffer)})`);
      }
      this.buffer += this.decoder.decode(read.value, { stream: true });
    }
  }

  static parse(block) {
    if (block.startsWith(":")) return { comment: block.slice(1).trim() };
    const frame = { id: null, event: "message", data: "" };
    for (const line of block.split("\n")) {
      const colon = line.indexOf(":");
      if (colon === -1) continue;
      const field = line.slice(0, colon);
      const value = line.slice(colon + 1).replace(/^ /, "");
      if (field === "id") frame.id = Number(value);
      else if (field === "event") frame.event = value;
      else if (field === "data") frame.data += value;
    }
    return frame;
  }

  async close() {
    this.controller?.abort();
    try {
      await this.reader.cancel();
    } catch {
      // already torn down by the abort
    }
  }
}

async function publish(topic, data) {
  const response = await fetch(`${base}/publish`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ topic, data }),
  });
  const body = await response.json();
  return { status: response.status, body };
}

async function main() {
  console.log(`contract: ${base}`);

  const health = await fetch(`${base}/health`);
  const healthBody = await health.json();
  assert(health.status === 200, "health answers 200", String(health.status));
  assert(healthBody.status === "ok", "health says ok", JSON.stringify(healthBody));
  assert(healthBody.subscribers === 0, "no subscribers yet", JSON.stringify(healthBody));

  const stream = await Stream.open(`${base}/events?topic=metrics`);
  assert(
    stream.response.headers.get("content-type").startsWith("text/event-stream"),
    "stream content-type is text/event-stream",
    stream.response.headers.get("content-type"),
  );

  const first = await publish("metrics", { n: 1 });
  assert(first.status === 202 && first.body.id === 1, "publish answers 202 with id 1", JSON.stringify(first));
  const other = await publish("other", { n: 2 });
  assert(other.body.id === 2, "second publish gets id 2", JSON.stringify(other));
  const third = await publish("metrics", { n: 3 });
  assert(third.body.id === 3, "third publish gets id 3", JSON.stringify(third));

  const frameOne = await stream.next();
  assert(frameOne.event === "metrics" && frameOne.id === 1, "subscriber sees id 1 under its topic", JSON.stringify(frameOne));
  assert(frameOne.data === '{"n":1}', "payload arrives JSON-encoded", frameOne.data);

  const frameThree = await stream.next();
  assert(frameThree.id === 3, "the topic filter skipped id 2 and delivered id 3", JSON.stringify(frameThree));

  const during = await (await fetch(`${base}/health`)).json();
  assert(during.subscribers === 1, "health counts the open stream", JSON.stringify(during));

  await stream.close();
  await sleep(150);

  const after = await (await fetch(`${base}/health`)).json();
  assert(after.subscribers === 0, "a closed stream frees its slot", JSON.stringify(after));

  const resumed = await Stream.open(`${base}/events?topic=metrics`, { "last-event-id": "2" });
  const replay = await resumed.next();
  assert(replay.id === 3, "Last-Event-ID 2 replays id 3 and nothing else", JSON.stringify(replay));
  await resumed.close();

  const missing = await fetch(`${base}/nope`);
  const missingBody = await missing.json();
  assert(missing.status === 404, "unknown route is 404", String(missing.status));
  assert(missingBody.error === "not_found", "404 body names the error", JSON.stringify(missingBody));

  const wrongMethod = await fetch(`${base}/health`, { method: "POST" });
  assert(wrongMethod.status === 405, "POST /health is 405", String(wrongMethod.status));

  const badTopic = await fetch(`${base}/events?topic=${encodeURIComponent("bad topic")}`);
  assert(badTopic.status === 400, "a topic with a space is refused before the stream opens", String(badTopic.status));

  const badJson = await fetch(`${base}/publish`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: "{not json",
  });
  assert(badJson.status === 400, "invalid JSON is 400", String(badJson.status));

  if (expectHeartbeat) {
    const beating = await Stream.open(`${base}/events`);
    const beat = await beating.next(4000);
    assert(beat.comment === "ping", "an idle stream receives a heartbeat comment", JSON.stringify(beat));
    await beating.close();
  }

  console.log(`contract: ${checks} checks passed`);
}

main().catch((err) => {
  console.error(`contract failed: ${err.message}`);
  process.exit(1);
});
