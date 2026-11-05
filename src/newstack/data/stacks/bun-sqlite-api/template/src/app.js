// app.js — the HTTP contract, framework-free. Exports buildRoutes(db) which
// returns a Bun.serve `routes` object plus a `fallback` for 404/405, and
// helpers shared by --selftest.
export const NOTE_KEYS = ["id", "title", "body", "created_at"];

// --- helpers ---------------------------------------------------------------

export function isValidId(raw) {
  return typeof raw === "string" && /^\d+$/.test(raw) && Number(raw) >= 1;
}

export function validateTitle(value) {
  if (typeof value !== "string" || value.trim() === "") {
    return { ok: false, detail: "title: must not be blank" };
  }
  return { ok: true, title: value };
}

export function validateBody(value) {
  if (value === undefined || value === null) return { ok: true, body: "" };
  if (typeof value !== "string") return { ok: false, detail: "body: must be a string" };
  return { ok: true, body: value };
}

// Rows come back from sqlite with id as a number (INTEGER PRIMARY KEY), which
// is what the contract wants; shape pins the key ORDER (JSON key order is
// insertion order, and the contract fixes it: id,title,body,created_at).
export function noteShape(row) {
  return {
    id: Number(row.id),
    title: row.title,
    body: row.body,
    created_at: row.created_at,
  };
}

// The statement cache: prepare ONCE per connection and reuse. Re-preparing
// per-request is measurably slower and, with named statements, throws on the
// second prepare of the same name.
export function prepareAll(db) {
  return {
    insert: db.prepare(
      "INSERT INTO notes (title, body, created_at) VALUES (?1, ?2, ?3) RETURNING *"
    ),
    list: db.prepare("SELECT * FROM notes ORDER BY id ASC"),
    get: db.prepare("SELECT * FROM notes WHERE id = ?"),
    patch: db.prepare(
      "UPDATE notes SET title = ?2, body = ?3 WHERE id = ?1 RETURNING *"
    ),
    del: db.prepare("DELETE FROM notes WHERE id = ?"),
    count: db.prepare("SELECT COUNT(*) AS n FROM notes"),
  };
}

// 404 detection for mutations: sqlite .run() returns {changes, lastInsertRowid}
// and NEVER returns the missing row, so "was it there" === changes === 0.
export function deletedCount(result) {
  return Number(result.changes);
}

const json = (value, status) => Response.json(value, { status });
const empty = (status) => new Response(null, { status });
const notFoundNote = (id) => json({ error: "not_found", detail: `no note with id ${id}` }, 404);
const notFoundRoute = (method, path) =>
  json({ error: "not_found", detail: `no route for ${method} ${path}` }, 404);
const invalidRequest = (detail) => json({ error: "invalid_request", detail }, 422);
const invalidJson = () => json({ error: "invalid_json" }, 422);

// Parse body once: undefined = empty body, null-throws path via catch.
async function readJson(req) {
  const text = await req.text();
  if (text.trim() === "") return { ok: true, data: {} };
  try {
    const data = JSON.parse(text);
    if (data === null || typeof data !== "object" || Array.isArray(data)) {
      return { ok: false, kind: "invalid_request", detail: "body: must be a JSON object" };
    }
    return { ok: true, data };
  } catch {
    return { ok: false, kind: "invalid_json" };
  }
}

// --- wiring ------------------------------------------------------------------

export function buildRoutes(db) {
  const q = prepareAll(db);

  return {
    routes: {
      "/health": {
        GET: () => json({ status: "ok", notes: Number(q.count.get().n) }, 200),
      },
      "/notes": {
        async POST(req) {
          const parsed = await readJson(req);
          if (!parsed.ok)
            return parsed.kind === "invalid_json"
              ? invalidJson()
              : invalidRequest(parsed.detail);
          const t = validateTitle(parsed.data.title);
          if (!t.ok) return invalidRequest(t.detail);
          const b = validateBody(parsed.data.body);
          if (!b.ok) return invalidRequest(b.detail);
          const row = q.insert.get(t.title, b.body, new Date().toISOString());
          return json(noteShape(row), 201);
        },
        GET: () => json({ notes: q.list.all().map(noteShape) }, 200),
      },
      "/notes/:id": {
        GET(req) {
          const id = req.params.id;
          if (!isValidId(id)) return notFoundNote(id);
          const row = q.get.get(Number(id));
          return row ? json(noteShape(row), 200) : notFoundNote(id);
        },
        async PATCH(req) {
          const id = req.params.id;
          if (!isValidId(id)) return notFoundNote(id);
          const existing = q.get.get(Number(id));
          if (!existing) return notFoundNote(id);
          const parsed = await readJson(req);
          if (!parsed.ok)
            return parsed.kind === "invalid_json"
              ? invalidJson()
              : invalidRequest(parsed.detail);
          let title = existing.title;
          let body = existing.body;
          if ("title" in parsed.data) {
            const t = validateTitle(parsed.data.title);
            if (!t.ok) return invalidRequest(t.detail);
            title = t.title;
          }
          if ("body" in parsed.data) {
            const b = validateBody(parsed.data.body);
            if (!b.ok) return invalidRequest(b.detail);
            body = b.body;
          }
          // created_at is NOT touched — PATCH must preserve it.
          const row = q.patch.get(Number(id), title, body);
          return json(noteShape(row), 200);
        },
        DELETE(req) {
          const id = req.params.id;
          if (!isValidId(id)) return notFoundNote(id);
          const res = q.del.run(Number(id));
          return deletedCount(res) === 0 ? notFoundNote(id) : empty(204);
        },
      },
    },

    // Bun routes only fire for declared method keys; everything else lands
    // here. Known paths with a wrong verb => 405, unknown path => 404 with
    // the query string stripped from the echo.
    fallback(req) {
      const url = new URL(req.url);
      const path = url.pathname;
      const known =
        path === "/health" ||
        path === "/notes" ||
        (/^\/notes\/[^/]+$/.test(path) && path !== "/notes/");
      if (known) return json({ error: "method_not_allowed" }, 405);
      return notFoundRoute(req.method, path);
    },
  };
}
