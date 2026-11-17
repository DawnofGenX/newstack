import assert from "node:assert/strict";
import { test } from "node:test";

import { createServer } from "../src/server.js";

/// Start a server on an ephemeral port, hand it to the test, always stop it.
async function withServer(options, run) {
  const server = createServer(options);
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const base = `http://127.0.0.1:${server.address().port}`;
  try {
    await run(base, server);
  } finally {
    // Open SSE streams are open connections: close() alone would wait forever.
    server.closeAllConnections?.();
    await new Promise((resolve) => server.close(resolve));
  }
}

/// An SSE stream read frame by frame. The reader is cancelled by close(), so a
/// test that fails an assertion cannot leave a socket behind.
async function openStream(url, headers = {}) {
  const controller = new AbortController();
  const response = await fetch(url, { headers, signal: controller.signal });
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  return {
    response,
    async next(ms = 3000) {
      const deadline = Date.now() + ms;
      for (;;) {
        const boundary = buffer.indexOf("\n\n");
        if (boundary !== -1) {
          const block = buffer.slice(0, boundary);
          buffer = buffer.slice(boundary + 2);
          return block;
        }
        const remaining = deadline - Date.now();
        if (remaining <= 0) throw new Error(`no frame within ${ms}ms: ${JSON.stringify(buffer)}`);
        const read = await Promise.race([
          reader.read(),
          new Promise((_, reject) => setTimeout(() => reject(new Error("read timed out")), remaining)),
        ]);
        if (read.done) throw new Error(`stream ended: ${JSON.stringify(buffer)}`);
        buffer += decoder.decode(read.value, { stream: true });
      }
    },
    async close() {
      controller.abort();
      try {
        await reader.cancel();
      } catch {
        // the abort already tore it down
      }
    },
  };
}

async function publish(base, topic, data) {
  const response = await fetch(`${base}/publish`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ topic, data }),
  });
  return { status: response.status, body: await response.json() };
}

test("health reports the counters", async () => {
  await withServer({}, async (base) => {
    const response = await fetch(`${base}/health`);
    assert.equal(response.status, 200);
    assert.deepEqual(await response.json(), { status: "ok", subscribers: 0, events: 0 });
  });
});

test("a subscriber receives what is published after it connects", async () => {
  await withServer({}, async (base) => {
    const stream = await openStream(`${base}/events?topic=metrics`);
    assert.match(stream.response.headers.get("content-type"), /^text\/event-stream/);

    const published = await publish(base, "metrics", { n: 1 });
    assert.equal(published.status, 202);
    assert.equal(published.body.id, 1);

    const frame = await stream.next();
    assert.match(frame, /^id: 1$/m);
    assert.match(frame, /^event: metrics$/m);
    assert.match(frame, /^data: \{"n":1\}$/m);
    await stream.close();
  });
});

test("the topic filter keeps other topics off the stream", async () => {
  await withServer({}, async (base) => {
    const stream = await openStream(`${base}/events?topic=metrics`);
    await publish(base, "other", { n: 1 });
    const published = await publish(base, "metrics", { n: 2 });
    const frame = await stream.next();
    assert.match(frame, new RegExp(`^id: ${published.body.id}$`, "m"));
    await stream.close();
  });
});

test("Last-Event-ID replays what the client missed, and only that", async () => {
  await withServer({}, async (base) => {
    await publish(base, "metrics", { n: 1 });
    const second = await publish(base, "metrics", { n: 2 });

    const stream = await openStream(`${base}/events?topic=metrics`, { "last-event-id": "1" });
    const frame = await stream.next();
    assert.match(frame, new RegExp(`^id: ${second.body.id}$`, "m"));
    assert.doesNotMatch(frame, /^id: 1$/m);
    await stream.close();
  });
});

test("the ?last_id= query is the curl-friendly spelling", async () => {
  await withServer({}, async (base) => {
    await publish(base, "metrics", { n: 1 });
    const second = await publish(base, "metrics", { n: 2 });
    const stream = await openStream(`${base}/events?last_id=1`);
    const frame = await stream.next();
    assert.match(frame, new RegExp(`^id: ${second.body.id}$`, "m"));
    await stream.close();
  });
});

test("a closed stream frees its slot", async () => {
  await withServer({}, async (base) => {
    const stream = await openStream(`${base}/events`);
    const open = await (await fetch(`${base}/health`)).json();
    assert.equal(open.subscribers, 1);
    await stream.close();

    let subscribers = open.subscribers;
    for (let i = 0; i < 40 && subscribers !== 0; i += 1) {
      await new Promise((r) => setTimeout(r, 25));
      subscribers = (await (await fetch(`${base}/health`)).json()).subscribers;
    }
    assert.equal(subscribers, 0);
  });
});

test("an idle stream receives a heartbeat comment", async () => {
  await withServer({ heartbeatMs: 25 }, async (base) => {
    const stream = await openStream(`${base}/events`);
    const frame = await stream.next(2000);
    assert.equal(frame, ": ping");
    await stream.close();
  });
});

test("a bad topic is refused before the stream opens", async () => {
  await withServer({}, async (base) => {
    const response = await fetch(`${base}/events?topic=${encodeURIComponent("bad topic")}`);
    assert.equal(response.status, 400);
    assert.equal((await response.json()).error, "bad_topic");
  });
});

test("invalid JSON and a missing topic are 400s", async () => {
  await withServer({}, async (base) => {
    const broken = await fetch(`${base}/publish`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: "{not json",
    });
    assert.equal(broken.status, 400);
    assert.equal((await broken.json()).error, "bad_json");

    const noTopic = await publish(base, undefined, { n: 1 });
    assert.equal(noTopic.status, 400);
    assert.equal(noTopic.body.error, "bad_topic");
  });
});

test("unknown routes are 404 and known routes reject the wrong method", async () => {
  await withServer({}, async (base) => {
    const missing = await fetch(`${base}/nope`);
    assert.equal(missing.status, 404);
    const body = await missing.json();
    assert.equal(body.error, "not_found");
    assert.match(body.detail, /no route for GET \/nope/);

    const wrong = await fetch(`${base}/health`, { method: "POST" });
    assert.equal(wrong.status, 405);
    assert.equal((await wrong.json()).allow, "GET");
  });
});

test("a subscriber that disconnects mid-publish does not break the others", async () => {
  await withServer({}, async (base) => {
    const leaver = await openStream(`${base}/events`);
    const stayer = await openStream(`${base}/events`);
    await leaver.close();
    await publish(base, "metrics", { n: 1 });
    const frame = await stayer.next();
    assert.match(frame, /^id: 1$/m);
    await stayer.close();
  });
});
