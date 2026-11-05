import assert from "node:assert/strict";
import test from "node:test";
import { WebSocket } from "ws";

import { createApp } from "../src/server.js";

function nextFrame(socket) {
  return new Promise((resolve, reject) => {
    socket.once("message", (data) => resolve(JSON.parse(data.toString("utf8"))));
    socket.once("error", reject);
  });
}

async function open(url) {
  const socket = new WebSocket(url);
  const joined = nextFrame(socket);
  await new Promise((resolve, reject) => {
    socket.once("open", resolve);
    socket.once("error", reject);
  });
  return { socket, joined: await joined };
}

test("a client joins, counts text, and leaves the presence room", async () => {
  const { server, sockets } = createApp();
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const { port } = server.address();
  const url = `ws://127.0.0.1:${port}/ws`;

  try {
    const health = await fetch(`http://127.0.0.1:${port}/health`);
    assert.equal(health.status, 200);
    assert.deepEqual(await health.json(), { status: "ok", clients: 0 });

    const first = await open(url);
    assert.deepEqual(first.joined, { type: "presence", event: "join", clients: 1 });

    const second = await open(url);
    assert.deepEqual(second.joined, { type: "presence", event: "join", clients: 2 });
    assert.deepEqual(await nextFrame(first.socket), {
      type: "presence",
      event: "join",
      clients: 2,
    });

    const answer = nextFrame(first.socket);
    first.socket.send(JSON.stringify({ type: "stats", text: "a b\nc\n" }));
    assert.deepEqual(await answer, { type: "stats", lines: 2, words: 3, bytes: 6 });

    const broken = nextFrame(first.socket);
    first.socket.send("{");
    assert.equal((await broken).code, "invalid_json");

    const leaving = nextFrame(first.socket);
    second.socket.close();
    assert.deepEqual(await leaving, { type: "presence", event: "leave", clients: 1 });

    const healthAfter = await (await fetch(`http://127.0.0.1:${port}/health`)).json();
    assert.deepEqual(healthAfter, { status: "ok", clients: 1 });

    first.socket.close();
  } finally {
    for (const client of sockets.clients) client.terminate();
    await new Promise((resolve) => server.close(resolve));
  }
});

test("an unknown path never upgrades and answers JSON 404", async () => {
  const { server, sockets } = createApp();
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const { port } = server.address();

  try {
    const response = await fetch(`http://127.0.0.1:${port}/nope`);
    assert.equal(response.status, 404);
    assert.deepEqual(await response.json(), {
      error: "not_found",
      detail: "no route for GET /nope",
    });

    const upgraded = new WebSocket(`ws://127.0.0.1:${port}/other`);
    await assert.rejects(
      new Promise((resolve, reject) => {
        upgraded.once("open", resolve);
        upgraded.once("error", reject);
      }),
      /Unexpected server response: 404/,
    );

    const wrongMethod = await fetch(`http://127.0.0.1:${port}/health`, { method: "POST" });
    assert.equal(wrongMethod.status, 405);
  } finally {
    for (const client of sockets.clients) client.terminate();
    await new Promise((resolve) => server.close(resolve));
  }
});
