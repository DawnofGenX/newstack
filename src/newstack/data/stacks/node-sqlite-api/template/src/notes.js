import { DatabaseSync } from 'node:sqlite';

export function openDatabase(path = process.env.DB_PATH || ':memory:') {
  const db = new DatabaseSync(path);
  db.exec(`
    CREATE TABLE IF NOT EXISTS notes (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT NOT NULL,
      body TEXT NOT NULL,
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
  `);
  return db;
}

export function listNotes(db) {
  return db.prepare('SELECT id, title, body, created_at AS createdAt FROM notes ORDER BY id').all();
}

export function createNote(db, title, body) {
  const info = db.prepare('INSERT INTO notes (title, body) VALUES (?, ?)').run(title, body);
  return db.prepare('SELECT id, title, body, created_at AS createdAt FROM notes WHERE id = ?').get(info.lastInsertRowid);
}

export function deleteNote(db, id) {
  const info = db.prepare('DELETE FROM notes WHERE id = ?').run(id);
  return info.changes > 0;
}

export function countNotes(db) {
  return db.prepare('SELECT COUNT(*) AS n FROM notes').get().n;
}