-- One migration, applied through sqlx's embedded migrator (compile-time
-- `sqlx::migrate!("./migrations")`), which records each file in
-- `_sqlx_migrations` in a transaction: re-running is a no-op, not a duplicate.
CREATE TABLE IF NOT EXISTS notes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    title      TEXT    NOT NULL CHECK (length(trim(title)) > 0),
    body       TEXT    NOT NULL DEFAULT '',
    created_at TEXT    NOT NULL,
    updated_at TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS notes_created_at ON notes (created_at, id);
