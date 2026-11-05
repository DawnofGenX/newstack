-- SQLite can add a column with a default in place; it cannot drop one before 3.35.
ALTER TABLE notes ADD COLUMN pinned INTEGER NOT NULL DEFAULT 0;
