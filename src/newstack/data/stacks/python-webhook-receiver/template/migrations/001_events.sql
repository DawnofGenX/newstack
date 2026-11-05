CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    received_at TEXT NOT NULL,
    body TEXT NOT NULL,
    signature TEXT NOT NULL
);
