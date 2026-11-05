import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import type { AddressInfo } from 'node:net';
import type { Server } from 'node:http';
import { buildApp } from '../src/app';
import { createDb, type NoteStore } from '../src/db';

let server: Server;
let base = '';
let db: NoteStore;

type J = Record<string, any>;
const json = { 'content-type': 'application/json' };
async function j(res: Response): Promise<J> {
  return (await res.json()) as J;
}

async function api(method: string, path: string, body?: unknown): Promise<Response> {
  return fetch(base + path, {
    method,
    headers: json,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

before(async () => {
  db = createDb();
  server = buildApp(db).listen(0, '127.0.0.1');
  await new Promise<void>((r) => server.once('listening', () => r()));
  base = 'http://127.0.0.1:' + (server.address() as AddressInfo).port;
});

after(async () => {
  await new Promise<void>((r) => server.close(() => r()));
  await db.disconnect();
});

test('GET /health returns ok + notes count', async () => {
  const res = await api('GET', '/health');
  assert.equal(res.status, 200);
  const body = await j(res);
  assert.equal(body.status, 'ok');
  assert.equal(typeof body.notes, 'number');
});

test('POST /notes creates a note with 201 and echoes title/body', async () => {
  const res = await api('POST', '/notes', { title: 'first', body: 'hello' });
  assert.equal(res.status, 201);
  const note = await j(res);
  assert.equal(note.title, 'first');
  assert.equal(note.body, 'hello');
  assert.equal(typeof note.id, 'number');
});

test('POST /notes without body defaults body to empty string', async () => {
  const res = await api('POST', '/notes', { title: 'no-body' });
  assert.equal(res.status, 201);
  const note = await j(res);
  assert.equal(note.body, '');
});

test('POST /notes with blank title -> 422 invalid_title', async () => {
  for (const title of ['', '   ']) {
    const res = await api('POST', '/notes', { title, body: 'x' });
    assert.equal(res.status, 422);
    assert.deepEqual(await j(res), { error: 'invalid_title' });
  }
});

test('POST /notes with missing title -> 422 invalid_title', async () => {
  const res = await api('POST', '/notes', { body: 'orphan' });
  assert.equal(res.status, 422);
  assert.deepEqual(await j(res), { error: 'invalid_title' });
});

test('GET /notes lists notes ordered by id ascending with exact keys', async () => {
  await api('POST', '/notes', { title: 'a', body: '' });
  await api('POST', '/notes', { title: 'b', body: '' });
  const res = await api('GET', '/notes');
  assert.equal(res.status, 200);
  const list = (await j(res)) as unknown as J[];
  assert.ok(Array.isArray(list) && list.length >= 2);
  const ids = list.map((n) => n.id as number);
  assert.deepEqual(ids, [...ids].sort((x, y) => x - y));
  for (const n of list) assert.deepEqual(Object.keys(n).sort(), ['body', 'id', 'title']);
});

test('GET /notes/:id 200 for existing, 404 shape for missing', async () => {
  const created = await j(await api('POST', '/notes', { title: 'peek', body: 'p' }));
  const hit = await api('GET', '/notes/' + created.id);
  assert.equal(hit.status, 200);
  assert.equal((await j(hit)).title, 'peek');
  const miss = await api('GET', '/notes/99999999');
  assert.equal(miss.status, 404);
  assert.deepEqual(await j(miss), { error: 'not_found', detail: 'no note with id 99999999' });
});

test('PATCH /notes/:id updates one field and preserves the other', async () => {
  const created = await j(await api('POST', '/notes', { title: 'orig', body: 'keep-me' }));
  const res = await api('PATCH', '/notes/' + created.id, { title: 'renamed' });
  assert.equal(res.status, 200);
  const note = await j(res);
  assert.equal(note.title, 'renamed');
  assert.equal(note.body, 'keep-me');
});

test('PATCH /notes/:id on missing id -> 404', async () => {
  const res = await api('PATCH', '/notes/99999999', { title: 'ghost' });
  assert.equal(res.status, 404);
  assert.equal((await j(res)).error, 'not_found');
});

test('DELETE /notes/:id -> 204 empty body, then GET -> 404', async () => {
  const created = await j(await api('POST', '/notes', { title: 'doomed', body: '' }));
  const del = await api('DELETE', '/notes/' + created.id);
  assert.equal(del.status, 204);
  assert.equal(await del.text(), '');
  const after = await api('GET', '/notes/' + created.id);
  assert.equal(after.status, 404);
});

test('wrong method on /health and /notes -> 405 method_not_allowed', async () => {
  for (const [method, path] of [
    ['POST', '/health'],
    ['DELETE', '/health'],
    ['PUT', '/notes'],
    ['PATCH', '/health'],
  ] as const) {
    const res = await api(method, path);
    assert.equal(res.status, 405, `${method} ${path}`);
    assert.deepEqual(await j(res), { error: 'method_not_allowed' });
  }
});

test('malformed JSON body -> 422 invalid_json', async () => {
  const res = await fetch(base + '/notes', {
    method: 'POST',
    headers: json,
    body: '{"title": "broken',
  });
  assert.equal(res.status, 422);
  assert.deepEqual(await j(res), { error: 'invalid_json' });
});

test('unknown path -> 404 not_found with METHOD PATH detail, query stripped', async () => {
  const res = await api('GET', '/nope?x=1');
  assert.equal(res.status, 404);
  assert.deepEqual(await j(res), { error: 'not_found', detail: 'no route for GET /nope' });
});

test('notes persist through a second PrismaClient on the same SQLite file', async () => {
  const created = await j(await api('POST', '/notes', { title: 'durable', body: 'rows' }));
  const db2 = createDb(); // fresh client, same file => survives process restart
  const rows = await db2.list();
  assert.ok(rows.some((n) => n.id === created.id && n.title === 'durable'));
  await db2.disconnect();
});
