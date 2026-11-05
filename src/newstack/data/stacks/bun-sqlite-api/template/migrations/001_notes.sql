-- 001_notes.sql — idempotent schema migration for the notes probe.
-- Applied once at startup inside a transaction; tracked in _migrations so a
-- second application is a no-op (it must never fail and never duplicate).
CREATE TABLE IF NOT EXISTS notes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL CHECK (length(trim(title)) > 0),
  body TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS _migrations (
  name TEXT PRIMARY KEY,
  applied_at TEXT NOT NULL
);
