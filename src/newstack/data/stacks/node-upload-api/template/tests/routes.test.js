// Wire-level tests: a real server on port 0 and real fetch calls, so the tests
// exercise Node's parser, chunk boundaries and the response headers.
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdtemp, rm } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import { UploadStore } from "../src/store.js";
import { createServer, listen, stop } from "../src/server.js";

async function withServer(fn) {
  const root = await mkdtemp(path.join(os.tmpdir(), "upload-test-"));
  const store = await UploadStore.open(root);
  const server = await createServer(store);
  const port = await listen(server, "127.0.0.1", 0);
  const base = `http://127.0.0.1:${port}`;
  try {
    await fn({ base, store, root });
  } finally {
    await stop(server);
    await rm(root, { recursive: true, force: true });
  }
}

async function create(base, name, size) {
  const response = await fetch(`${base}/uploads`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, size }),
  });
  return { status: response.status, body: await response.json() };
}

function put(base, id, offset, bytes) {
  return fetch(`${base}/uploads/${id}?offset=${offset}`, {
    method: "PUT",
    headers: { "Content-Type": "application/octet-stream" },
    body: bytes,
  });
}

test("health reports an empty service", async () => {
  await withServer(async ({ base }) => {
    const response = await fetch(`${base}/health`);
    assert.equal(response.status, 200);
    assert.deepEqual(await response.json(), { status: "ok", sessions: 0 });
  });
});

test("creating an upload returns an id and a zero offset", async () => {
  await withServer(async ({ base }) => {
    const { status, body } = await create(base, "notes.txt", 11);
    assert.equal(status, 201);
    assert.match(body.id, /^[0-9a-f]{16}$/);
    assert.equal(body.name, "notes.txt");
    assert.equal(body.size, 11);
    assert.equal(body.received, 0);
    assert.equal(body.offset, 0);
    assert.equal(body.complete, false);
  });
});

test("creation validates the name, size and body", async () => {
  await withServer(async ({ base }) => {
    const cases = [
      [{ size: 4 }, 422, "missing_name"],
      [{ name: "   ", size: 4 }, 422, "missing_name"],
      [{ name: "a.txt", size: 0 }, 422, "invalid_size"],
      [{ name: "a.txt", size: 2.5 }, 422, "invalid_size"],
      [{ name: "a.txt", size: "4" }, 422, "invalid_size"],
      [{ name: "a.txt", size: 2 * 1024 * 1024 }, 413, "too_large"],
    ];
    for (const [payload, status, error] of cases) {
      const response = await fetch(`${base}/uploads`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      assert.equal(response.status, status, JSON.stringify(payload));
      assert.equal((await response.json()).error, error, JSON.stringify(payload));
    }
    const broken = await fetch(`${base}/uploads`, { method: "POST", body: "{oops" });
    assert.equal(broken.status, 422);
    assert.equal((await broken.json()).error, "invalid_json");
  });
});

test("a two-chunk upload reports a digest of the whole file", async () => {
  await withServer(async ({ base }) => {
    const payload = Buffer.from("hello resumable world\n");
    const { body } = await create(base, "notes.txt", payload.length);

    const first = await put(base, body.id, 0, payload.subarray(0, 8));
    assert.equal(first.status, 200);
    const partial = await first.json();
    assert.equal(partial.received, 8);
    assert.equal(partial.offset, 8);
    assert.equal(partial.complete, false);
    assert.equal(partial.sha256, undefined);

    const second = await put(base, body.id, 8, payload.subarray(8));
    assert.equal(second.status, 200);
    const done = await second.json();
    assert.equal(done.received, payload.length);
    assert.equal(done.complete, true);
    assert.equal(done.sha256, createHash("sha256").update(payload).digest("hex"));

    const content = await fetch(`${base}/uploads/${body.id}/content`);
    assert.equal(content.status, 200);
    assert.equal(content.headers.get("content-type"), "application/octet-stream");
    assert.equal(content.headers.get("x-content-sha256"), done.sha256);
    assert.deepEqual(Buffer.from(await content.arrayBuffer()), payload);
  });
});

test("a wrong offset is refused with the expected value", async () => {
  await withServer(async ({ base }) => {
    const { body } = await create(base, "a.bin", 10);
    const response = await put(base, body.id, 4, Buffer.from("abcd"));
    assert.equal(response.status, 409);
    const payload = await response.json();
    assert.equal(payload.error, "offset_mismatch");
    assert.equal(payload.expected, 0);
    assert.equal(payload.got, 4);
  });
});

test("an offset must be a byte count", async () => {
  await withServer(async ({ base }) => {
    const { body } = await create(base, "a.bin", 10);
    for (const raw of ["", "-1", "1.5", "abc"]) {
      const response = await put(base, body.id, raw, Buffer.from("x"));
      assert.equal(response.status, 422, `offset=${raw}`);
      assert.equal((await response.json()).error, "invalid_offset", `offset=${raw}`);
    }
  });
});

test("a chunk beyond the declared size is refused and nothing is stored", async () => {
  await withServer(async ({ base }) => {
    const { body } = await create(base, "a.bin", 4);
    const response = await put(base, body.id, 0, Buffer.from("too long"));
    assert.equal(response.status, 413);
    assert.equal((await response.json()).error, "too_large");

    const status = await fetch(`${base}/uploads/${body.id}`);
    assert.equal((await status.json()).received, 0);
  });
});

test("an empty chunk is refused", async () => {
  await withServer(async ({ base }) => {
    const { body } = await create(base, "a.bin", 4);
    const response = await put(base, body.id, 0, Buffer.alloc(0));
    assert.equal(response.status, 422);
    assert.equal((await response.json()).error, "empty_chunk");
  });
});

test("content before completion is a conflict, not an empty file", async () => {
  await withServer(async ({ base }) => {
    const { body } = await create(base, "a.bin", 6);
    await put(base, body.id, 0, Buffer.from("abc"));
    const response = await fetch(`${base}/uploads/${body.id}/content`);
    assert.equal(response.status, 409);
    const payload = await response.json();
    assert.equal(payload.error, "incomplete");
    assert.equal(payload.received, 3);
    assert.equal(payload.size, 6);
  });
});

test("deleting an upload removes the record and the bytes", async () => {
  await withServer(async ({ base }) => {
    const { body } = await create(base, "a.bin", 3);
    await put(base, body.id, 0, Buffer.from("abc"));

    const deleted = await fetch(`${base}/uploads/${body.id}`, { method: "DELETE" });
    assert.equal(deleted.status, 204);
    assert.equal(await deleted.text(), "");

    const again = await fetch(`${base}/uploads/${body.id}`);
    assert.equal(again.status, 404);
    assert.equal((await again.json()).error, "unknown_upload");
  });
});

test("unknown ids, paths and methods have their own answers", async () => {
  await withServer(async ({ base }) => {
    const missing = await fetch(`${base}/uploads/deadbeefdeadbeef`);
    assert.equal(missing.status, 404);
    assert.equal((await missing.json()).error, "unknown_upload");

    const nowhere = await fetch(`${base}/nope`);
    assert.equal(nowhere.status, 404);
    assert.deepEqual(await nowhere.json(), {
      error: "not_found",
      detail: "no route for GET /nope",
    });

    const wrong = await fetch(`${base}/health`, { method: "POST" });
    assert.equal(wrong.status, 405);
    assert.equal((await wrong.json()).error, "method_not_allowed");

    const putHealth = await fetch(`${base}/uploads`, { method: "GET" });
    assert.equal(putHealth.status, 405);
  });
});

test("a restarted store keeps every received byte", async () => {
  await withServer(async ({ base, root, store }) => {
    const { body } = await create(base, "a.bin", 8);
    await put(base, body.id, 0, Buffer.from("1234"));
    await store.save();

    const reopened = await UploadStore.open(root);
    const session = reopened.get(body.id);
    assert.equal(session.received, 4);
    assert.equal(session.complete, false);

    // The running hash was lost with the process, so the next chunk has to be
    // hashed together with the bytes already on disk.
    await reopened.write(session, Buffer.from("5678"));
    assert.equal(session.complete, true);
    assert.equal(session.digest, createHash("sha256").update("12345678").digest("hex"));
  });
});
