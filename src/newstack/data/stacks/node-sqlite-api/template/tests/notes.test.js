import { test } from 'node:test';
import assert from 'node:assert/strict';
import { openDatabase, listNotes, createNote, deleteNote, countNotes } from '../src/notes.js';

test('create and list notes', () => {
  const db = openDatabase(':memory:');
  const note = createNote(db, 'hello', 'world');
  assert.equal(note.title, 'hello');
  assert.equal(note.body, 'world');
  assert.equal(typeof note.id, 'number');
  assert.deepEqual(listNotes(db).map((n) => n.title), ['hello']);
  assert.equal(countNotes(db), 1);
});

test('delete note returns false when missing', () => {
  const db = openDatabase(':memory:');
  const note = createNote(db, 'a', 'b');
  assert.equal(deleteNote(db, note.id), true);
  assert.equal(deleteNote(db, note.id), false);
  assert.equal(countNotes(db), 0);
});