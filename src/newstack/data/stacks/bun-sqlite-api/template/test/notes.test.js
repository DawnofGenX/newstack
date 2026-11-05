// svc.test.js — bun:test suite. Real server on port 0 (ephemeral) + a real
// restart-persistence proof against a temp-file DB.
import { describe, it, expect, beforeAll, afterAll } from "bun:test";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { openDb, migrate } from "../src/db.js";
import { buildRoutes } from "../src/app.js";

const dir = mkdtempSync(join(tmpdir(), "bunsql-test-"));
const dbPath = join(dir, "test.db");

function boot(dbFile) {
  const db = openDb(dbFile);
  migrate(db);
  const { routes, fallback } = buildRoutes(db);
  const server = Bun.serve({ hostname: "127.0.0.1", port: 0, routes, fetch: fallback });
  return {
    base: `http://127.0.0.1:${server.port}`,
    stop: () => {
      server.stop(true);
      db.close();
    },
  };
}

let svc;
let base;
beforeAll(() => {
  svc = boot(dbPath);
  base = svc.base;
});
afterAll(() => {
  svc.stop();
  rmSync(dir, { recursive: true, force: true });
});

const get = (p) => fetch(base + p);
const send = (m, p, body) =>
  fetch(base + p, {
    method: m,
    body: typeof body === "string" ? body : JSON.stringify(body),
  });
const KEY_ORDER = '["id","title","body","created_at"]';

describe("health and listing", () => {
  it("GET /health reports ok + live count", async () => {
    const r = await get("/health");
    expect(r.status).toBe(200);
    const j = await r.json();
    expect(j.status).toBe("ok");
    expect(typeof j.notes).toBe("number");
  });
  it("GET /notes on a clean store lists oldest-first under the wrapper", async () => {
    const r = await get("/notes");
    expect(r.status).toBe(200);
    const j = await r.json();
    expect(Array.isArray(j.notes)).toBe(true);
    expect(j.notes.length).toBe(0);
  });
});

describe("create", () => {
  it("POST /notes returns 201 with exact key order", async () => {
    const r = await send("POST", "/notes", { title: "shopping", body: "milk" });
    expect(r.status).toBe(201);
    const text = await r.text();
    expect(Object.keys(JSON.parse(text))).toEqual(["id", "title", "body", "created_at"]);
    expect(text.indexOf('"id"')).toBe(1); // {"id" first — order pinned by contract
    const j = JSON.parse(text);
    expect(j.id).toBe(1);
    expect(j.title).toBe("shopping");
    expect(j.body).toBe("milk");
    expect(j.created_at).toMatch(/^\d{4}-\d{2}-\d{2}T.*Z$/);
  });
  it("body defaults to empty string", async () => {
    const r = await send("POST", "/notes", { title: "bare" });
    expect(r.status).toBe(201);
    expect((await r.json()).body).toBe("");
  });
  it("blank/whitespace title -> 422 exact detail", async () => {
    for (const t of ["", "   ", "\t"]) {
      const r = await send("POST", "/notes", { title: t });
      expect(r.status).toBe(422);
      expect(await r.json()).toEqual({ error: "invalid_request", detail: "title: must not be blank" });
    }
  });
  it("missing title -> 422", async () => {
    const r = await send("POST", "/notes", { body: "orphan" });
    expect(r.status).toBe(422);
  });
  it("bad JSON -> 422 invalid_json", async () => {
    const r = await send("POST", "/notes", "{oops");
    expect(r.status).toBe(422);
    expect(await r.json()).toEqual({ error: "invalid_json" });
  });
});

describe("read", () => {
  it("GET /notes/{id} returns the object; oldest-first listing", async () => {
    const r = await get("/notes/1");
    expect(r.status).toBe(200);
    const j = await r.json();
    expect(j.title).toBe("shopping");
    const list = await (await get("/notes")).json();
    expect(list.notes.map((x) => x.id)).toEqual([1, 2]);
  });
  it("missing id -> 404 with exact detail", async () => {
    const r = await get("/notes/99");
    expect(r.status).toBe(404);
    expect(await r.json()).toEqual({ error: "not_found", detail: "no note with id 99" });
  });
  it("non-numeric id -> 404, never a sqlite crash", async () => {
    const r = await get("/notes/abc");
    expect(r.status).toBe(404);
  });
});

describe("patch", () => {
  it("PATCH title-only preserves body and created_at", async () => {
    const before = (await (await get("/notes/1")).json()).created_at;
    const r = await send("PATCH", "/notes/1", { title: "renamed" });
    expect(r.status).toBe(200);
    const j = await r.json();
    expect(j.title).toBe("renamed");
    expect(j.body).toBe("milk");
    expect(j.created_at).toBe(before);
  });
  it("PATCH body-only preserves title", async () => {
    const r = await send("PATCH", "/notes/1", { body: "eggs" });
    expect((await r.json()).title).toBe("renamed");
  });
  it("PATCH blank title -> 422; bad JSON -> 422 invalid_json", async () => {
    expect((await send("PATCH", "/notes/1", { title: " " })).status).toBe(422);
    const bad = await send("PATCH", "/notes/1", "{");
    expect(bad.status).toBe(422);
    expect(await bad.json()).toEqual({ error: "invalid_json" });
  });
  it("PATCH missing id -> 404", async () => {
    expect((await send("PATCH", "/notes/9999", { title: "x" })).status).toBe(404);
  });
});

describe("delete", () => {
  it("DELETE -> 204 empty; second DELETE -> 404", async () => {
    const id = (await (await send("POST", "/notes", { title: "doomed" })).json()).id;
    const first = await send("DELETE", `/notes/${id}`);
    expect(first.status).toBe(204);
    expect(await first.text()).toBe("");
    const second = await send("DELETE", `/notes/${id}`);
    expect(second.status).toBe(404);
    expect((await second.json()).detail).toBe(`no note with id ${id}`);
  });
});

describe("routing edges", () => {
  it("wrong method on known path -> 405", async () => {
    for (const p of ["/notes", "/notes/1", "/health"]) {
      const r = await fetch(base + p, { method: "PUT" });
      expect(r.status).toBe(405);
      expect(await r.json()).toEqual({ error: "method_not_allowed" });
    }
  });
  it("unknown path -> 404 with method+path echo, query stripped", async () => {
    const r = await get("/zzz?x=1");
    expect(r.status).toBe(404);
    expect(await r.json()).toEqual({ error: "not_found", detail: "no route for GET /zzz" });
  });
});

describe("restart persistence", () => {
  it("rows survive a full server restart on the same DB file", async () => {
    const made = await (await send("POST", "/notes", { title: "survivor" })).json();
    svc.stop();
    const again = boot(dbPath); // same file, brand-new process-local state
    try {
      const j = await (await fetch(again.base + `/notes/${made.id}`)).json();
      expect(j.title).toBe("survivor");
      expect(j.created_at).toBe(made.created_at);
    } finally {
      again.stop();
      svc = boot(dbPath); // restore for any later hooks
      base = svc.base;
    }
  });
});
