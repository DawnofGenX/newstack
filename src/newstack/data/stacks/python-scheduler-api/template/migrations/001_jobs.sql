CREATE TABLE jobs (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    payload TEXT NOT NULL DEFAULT '',
    run_at REAL NOT NULL,
    interval_seconds REAL,
    status TEXT NOT NULL DEFAULT 'pending',
    attempts INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 3,
    locked_until REAL,
    last_error TEXT,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

CREATE INDEX jobs_due ON jobs (status, run_at);

CREATE TABLE runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL REFERENCES jobs (id) ON DELETE CASCADE,
    started_at REAL NOT NULL,
    finished_at REAL,
    status TEXT NOT NULL,
    lines INTEGER,
    words INTEGER,
    bytes INTEGER,
    error TEXT
);

CREATE INDEX runs_job ON runs (job_id, id);
