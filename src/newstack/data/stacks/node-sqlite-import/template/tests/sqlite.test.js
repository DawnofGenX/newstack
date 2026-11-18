import test from 'node:test';
import assert from 'node:assert/strict';
import { parseCsv } from '../src/sqlite.js';
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { importCsv, runQuery } from '../src/sqlite.js';

test('parseCsv basic', () => {
  const { header, rows } = parseCsv('a,b\n1,2\n3,4\n');
  assert.deepEqual(header, ['a', 'b']);
  assert.equal(rows.length, 2);
});

test('import and query', () => {
  const dir = mkdtempSync(join(tmpdir(), 'sq-'));
  const csv = join(dir, 'data.csv');
  const db = join(dir, 'data.db');
  writeFileSync(csv, 'name,age\nalice,30\nbob,25\n');
  importCsv(csv, db);
  const r = runQuery(db, 'SELECT name FROM data ORDER BY name');
  assert.equal(r.length, 2);
  assert.equal(r[0].name, 'alice');
  rmSync(dir, { recursive: true });
});
