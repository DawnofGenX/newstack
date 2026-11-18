import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { createHash } from "node:crypto";
import { DatabaseSync } from "node:sqlite";

export function openDatabase(dbPath) {
  return new DatabaseSync(dbPath);
}

export function ensureMigrationsTable(db) {
  db.exec(
    "CREATE TABLE IF NOT EXISTS _migrations (name TEXT PRIMARY KEY, checksum TEXT NOT NULL, applied_at TEXT NOT NULL)"
  );
}

export function checksumSql(sql) {
  return createHash("sha256").update(sql).digest("hex");
}

export function listMigrationFiles(dir) {
  return readdirSync(dir)
    .filter((f) => f.endsWith(".sql"))
    .sort();
}

export function appliedMigrationNames(db) {
  ensureMigrationsTable(db);
  return new Set(db.prepare("SELECT name FROM _migrations").all().map((r) => r.name));
}

export function applyMigrations({ dbPath, dir }) {
  const db = openDatabase(dbPath);
  ensureMigrationsTable(db);
  const applied = appliedMigrationNames(db);
  const results = [];
  for (const file of listMigrationFiles(dir)) {
    if (applied.has(file)) {
      results.push({ file, status: "skipped" });
      continue;
    }
    const sql = readFileSync(join(dir, file), "utf8");
    const checksum = checksumSql(sql);
    db.exec("BEGIN");
    try {
      db.exec(sql);
      db.prepare(
        "INSERT INTO _migrations (name, checksum, applied_at) VALUES (?, ?, ?)"
      ).run(file, checksum, new Date().toISOString());
      db.exec("COMMIT");
      results.push({ file, status: "applied" });
    } catch (err) {
      db.exec("ROLLBACK");
      db.close();
      throw err;
    }
  }
  db.close();
  return results;
}

export function migrationStatus({ dbPath, dir }) {
  const db = openDatabase(dbPath);
  ensureMigrationsTable(db);
  const applied = appliedMigrationNames(db);
  db.close();
  return listMigrationFiles(dir).map((file) => ({
    file,
    applied: applied.has(file),
  }));
}
