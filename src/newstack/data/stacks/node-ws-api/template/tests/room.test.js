import assert from "node:assert/strict";
import test from "node:test";

import { createRoom } from "../src/room.js";

function fakeSocket(sent) {
  const socket = {
    OPEN: 1,
    readyState: 1,
    sent,
    send(payload) {
      sent.push(JSON.parse(payload));
    },
  };
  return socket;
}

test("presence counts the member that just joined", () => {
  const room = createRoom();
  const sent = [];
  assert.deepEqual(room.add(1, fakeSocket(sent)), { type: "presence", event: "join", clients: 1 });
  assert.deepEqual(room.add(2, fakeSocket(sent)), { type: "presence", event: "join", clients: 2 });
  assert.deepEqual(room.remove(1), { type: "presence", event: "leave", clients: 1 });
  assert.equal(room.size, 1);
});

test("broadcast reaches every open member and skips closing ones", () => {
  const room = createRoom();
  const first = fakeSocket([]);
  const second = fakeSocket([]);
  const closing = fakeSocket([]);
  room.add(1, first);
  room.add(2, second);
  room.add(3, closing);
  closing.readyState = 2;

  room.broadcast({ type: "presence", event: "join", clients: 3 });

  assert.equal(first.sent.length, 1);
  assert.equal(second.sent.length, 1);
  assert.equal(closing.sent.length, 0);
});
