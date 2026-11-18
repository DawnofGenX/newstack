import { test, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { resolvers, resetNotes } from '../src/schema.js';

beforeEach(() => resetNotes());

test('Query.notes starts empty', () => {
  assert.deepEqual(resolvers.Query.notes(), []);
});

test('Mutation.addNote stores and returns a note', () => {
  const note = resolvers.Mutation.addNote(null, { title: 'hello', body: 'world' });
  assert.equal(note.title, 'hello');
  assert.equal(note.body, 'world');
  assert.equal(typeof note.id, 'number');
  assert.deepEqual(resolvers.Query.notes(), [note]);
});