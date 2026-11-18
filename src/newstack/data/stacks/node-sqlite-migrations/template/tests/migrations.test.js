import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { applyMigrations, migrationStatus } from "../src/migrations.js";

test("applies pending migrations and records them", () => {
  const dir = mkdtempSync(join(tmpdir(), "mig-"));
  const migDir = join(dir, "migrations");
  mkdirSync(migDir);
  writeFileSync(join(migDir, "001_create.sql"), "CREATE TABLE t (id INTEGER PRIMARY KEY, name TEXT);");
  writeFileSync(join(migDir, "002_seed.sql"), "INSERT INTO t (name) VALUES ('alice');");
  const dbPath = join(dir, "app.db");
  const first = applyMigrations({ dbPath, dir: migDir });
  assert.equal(first.length, 2);
  assert.equal(first[0].status, "applied");
  const second = applyMigrations({ dbPath, dir: migDir });
  assert.deepEqual(second.map((r) => r.status), ["skipped", "skipped"]);
  const st = migrationStatus({ dbPath, dir: migDir });
  assert.equal(st.filter((s) => s.applied).length, 2);
  rmSync(dir, { recursive: true, force: true });
});

test("rolls back a failed migration", () => {
  const dir = mkdtempSync(join(tmpdir(), "mig-"));
  const migDir = join(dir, "migrations");
  mkdirSync(migDir);
  writeFileSync(join(migDir, "001_bad.sql"), "CREATE TABLE nope (x INTEGER); INSERT INTO missing VALUES (1);");
  const dbPath = join(dir, "app.db");
  assert.throws(() => applyMigrations({ dbPath, dir: migDir }));
  rmSync(dir, { recursive: true, force: true });
});
