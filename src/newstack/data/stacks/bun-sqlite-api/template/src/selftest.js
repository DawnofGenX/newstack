// selftest.js — offline assertion suite: >=30 checks over counting,
// validation, JSON shape and SQL helpers. Never binds a socket.
import { Database } from "bun:sqlite";
import {
  isValidId,
  validateTitle,
  validateBody,
  noteShape,
  prepareAll,
  deletedCount,
} from "./app.js";
import { migrate, openDb } from "./db.js";

let n = 0;
function ok(cond, what) {
  n++;
  if (!cond) throw new Error(`selftest FAIL: ${what}`);
}
function eq(got, want, what) {
  ok(JSON.stringify(got) === JSON.stringify(want), `${what}: got ${JSON.stringify(got)} want ${JSON.stringify(want)}`);
}

export function runSelftest() {
  // --- isValidId ---------------------------------------------------------
  ok(isValidId("1") === true, "id 1 valid");
  ok(isValidId("42") === true, "id 42 valid");
  ok(isValidId("0") === false, "id 0 invalid");
  ok(isValidId("-3") === false, "negative invalid");
  ok(isValidId("1.5") === false, "float invalid");
  ok(isValidId("abc") === false, "word invalid");
  ok(isValidId("") === false, "empty invalid");
  ok(isValidId(" 7") === false, "padded invalid");

  // --- validateTitle -------------------------------------------------------
  ok(validateTitle("shopping").ok === true, "plain title ok");
  ok(validateTitle("x").ok === true, "single char ok");
  ok(validateTitle("").ok === false, "empty title rejected");
  ok(validateTitle("   ").ok === false, "whitespace title rejected");
  ok(validateTitle("\t\n").ok === false, "tab-newline title rejected");
  ok(validateTitle(undefined).ok === false, "missing title rejected");
  ok(validateTitle(42).ok === false, "numeric title rejected");
  ok(validateTitle("").detail === "title: must not be blank", "title detail text exact");

  // --- validateBody ---------------------------------------------------------
  eq(validateBody(undefined), { ok: true, body: "" }, "missing body defaults empty");
  eq(validateBody(null), { ok: true, body: "" }, "null body defaults empty");
  eq(validateBody("milk"), { ok: true, body: "milk" }, "string body kept");
  ok(validateBody(7).ok === false, "numeric body rejected");

  // --- noteShape --------------------------------------------------------------
  const shaped = noteShape({ id: 3, title: "t", body: "b", created_at: "C" });
  eq(Object.keys(shaped), ["id", "title", "body", "created_at"], "key order fixed");
  ok(typeof shaped.id === "number", "id numeric in output");

  // --- sqlite helpers on an in-memory db --------------------------------------
  const db = new Database(":memory:");
  db.exec(
    "CREATE TABLE notes (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL CHECK (length(trim(title)) > 0), body TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL)"
  );
  const q = prepareAll(db);
  ok(q && typeof q.insert.run === "function", "prepareAll returns statements");

  const ins = q.insert.get("shopping", "milk", "2020-01-01T00:00:00.000Z");
  eq(ins, { id: 1, title: "shopping", body: "milk", created_at: "2020-01-01T00:00:00.000Z" }, "insert RETURNING row");

  const del = q.del.run(1);
  ok(typeof del.changes === "number", "run().changes is a number");
  eq(deletedCount(del), 1, "delete hit reports 1");
  eq(deletedCount(q.del.run(1)), 0, "delete miss reports 0 -> 404 path");

  // CHECK constraint rejects blank titles at the SQL layer too
  let checkFired = false;
  try {
    db.run("INSERT INTO notes (title, body, created_at) VALUES ('  ','','x')");
  } catch {
    checkFired = true;
  }
  ok(checkFired, "SQL CHECK blocks blank title");

  // statement reuse: the SAME prepared statement, hammered
  for (let i = 0; i < 5; i++) q.insert.run("r" + i, "", "t");
  eq(Number(q.count.get().n), 5, "reused statement inserts 5");
  eq(q.list.all().map((r) => r.id), [2, 3, 4, 5, 6], "AUTOINCREMENT sequence");
  const patchRes = q.patch.get(3, "renamed", "b2");
  eq(patchRes, { id: 3, title: "renamed", body: "b2", created_at: "t" }, "patch keeps id, swaps fields");

  // openDb pragmas + migration idempotency on a temp file
  const path = `/tmp/bunsql-selftest-${process.pid}.db`;
  const live = openDb(path);
  eq(live.query("PRAGMA journal_mode").get(), { journal_mode: "wal" }, "WAL applied per connection");
  eq(live.query("PRAGMA busy_timeout").get(), { timeout: 5000 }, "busy_timeout 5000");
  eq(live.query("PRAGMA foreign_keys").get(), { foreign_keys: 1 }, "foreign_keys ON");
  const firstRun = migrate(live).length;
  ok(firstRun >= 1, "migration applied on fresh db");
  const secondRun = migrate(live).length;
  eq(secondRun, 0, "migration no-ops on second run");
  live.exec("INSERT INTO notes (title, body, created_at) VALUES ('a','','t')");
  const again = openDb(path); // new connection, same file
  eq(Number(again.query("SELECT COUNT(*) AS n FROM notes").get().n), 1, "row survives new connection");
  again.close();
  live.close();
  Bun.file(path).delete();

  return { checks: n };
}
