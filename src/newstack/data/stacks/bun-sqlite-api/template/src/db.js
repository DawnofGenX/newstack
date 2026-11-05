// db.js — connection + migration bootstrap shared by server, tests, selftest.
import { Database } from "bun:sqlite";
import { readdirSync, readFileSync } from "node:fs";

export const DEFAULT_DB_PATH = "./notes.db";

// Open a connection with the three PRAGMAs the contract demands, applied on
// EVERY connection. Note: bun:sqlite 1.4.2 has no `db.pragma()` helper —
// PRAGMA results must be read through `db.query(...)` or they are silently
// ignored when sent through `db.exec()`.
export function openDb(dbPath = process.env.DB_PATH || DEFAULT_DB_PATH) {
  const db = new Database(dbPath, { create: true });
  db.query("PRAGMA journal_mode = WAL").get();
  db.query("PRAGMA busy_timeout = 5000").get();
  db.query("PRAGMA foreign_keys = ON").get();
  return db;
}

// Idempotent migration runner. Reads migrations/NNN_name.sql files, applies
// each unseen one inside a single transaction, records it in _migrations.
// Re-running is a verified no-op; a failure rolls the whole file back.
export function migrate(db, migrationsDir = new URL("../migrations/", import.meta.url)) {
  db.exec(
    "CREATE TABLE IF NOT EXISTS _migrations (name TEXT PRIMARY KEY, applied_at TEXT NOT NULL);"
  );
  const seen = db.prepare("SELECT 1 FROM _migrations WHERE name = ?");
  const record = db.prepare("INSERT INTO _migrations (name, applied_at) VALUES (?, ?)");
  // Bun.scanDir / Bun.syncScanDirSync do not exist in 1.4.2 — node:fs it is.
  const dirPath = migrationsDir instanceof URL ? migrationsDir.pathname : migrationsDir;
  const files = readdirSync(dirPath)
    .filter((f) => f.endsWith(".sql"))
    .sort();
  const applied = [];
  for (const file of files) {
    if (seen.get(file) !== null) continue;
    // Read SQL synchronously BEFORE the transaction — async awaits inside
    // db.transaction() are a documented Bun footgun.
    const sql = readFileSync(dirPath + "/" + file, "utf8");
    const run = db.transaction(() => {
      db.exec(sql);
      record.run(file, new Date().toISOString());
    });
    run();
    applied.push(file);
  }
  return applied;
}
