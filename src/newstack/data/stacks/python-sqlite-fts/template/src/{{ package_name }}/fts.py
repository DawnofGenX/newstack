"""SQLite FTS5 helpers."""

from __future__ import annotations

import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL DEFAULT '',
    body TEXT NOT NULL DEFAULT ''
);

CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
    title, body, content='documents', content_rowid='id', tokenize='porter'
);

CREATE TRIGGER IF NOT EXISTS documents_ai AFTER INSERT ON documents BEGIN
    INSERT INTO documents_fts(rowid, title, body) VALUES (new.id, new.title, new.body);
END;
CREATE TRIGGER IF NOT EXISTS documents_ad AFTER DELETE ON documents BEGIN
    INSERT INTO documents_fts(documents_fts, rowid, title, body)
        VALUES ('delete', old.id, old.title, old.body);
END;
CREATE TRIGGER IF NOT EXISTS documents_au AFTER UPDATE ON documents BEGIN
    INSERT INTO documents_fts(documents_fts, rowid, title, body)
        VALUES ('delete', old.id, old.title, old.body);
    INSERT INTO documents_fts(rowid, title, body) VALUES (new.id, new.title, new.body);
END;
"""


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def add_document(conn: sqlite3.Connection, doc_id: int, title: str, body: str) -> None:
    conn.execute(
        "INSERT INTO documents(id, title, body) VALUES (?, ?, ?) "
        "ON CONFLICT(id) DO UPDATE SET title=excluded.title, body=excluded.body",
        (doc_id, title, body),
    )
    conn.commit()


def escape_query(query: str) -> str:
    # Quote each term so user input cannot inject FTS5 syntax.
    terms = [t for t in query.split() if t]
    if not terms:
        return '""'
    out = []
    for term in terms:
        safe = term.replace('"', '""')
        out.append(f'"{safe}"')
    return " ".join(out)


def search(conn: sqlite3.Connection, query: str, limit: int = 10) -> list[dict]:
    ensure_schema(conn)
    q = escape_query(query)
    rows = conn.execute(
        "SELECT d.id, d.title, d.body, "
        "bm25(documents_fts) AS score, "
        "snippet(documents_fts, 1, '[', ']', '...', 8) AS snip "
        "FROM documents_fts JOIN documents d ON d.id = documents_fts.rowid "
        "WHERE documents_fts MATCH ? "
        "ORDER BY bm25(documents_fts) "
        "LIMIT ?",
        (q, limit),
    ).fetchall()
    return [
        {
            "id": r["id"],
            "title": r["title"],
            "body": r["body"],
            "score": r["score"],
            "snippet": r["snip"],
        }
        for r in rows
    ]


def rebuild(conn: sqlite3.Connection) -> None:
    ensure_schema(conn)
    conn.execute("INSERT INTO documents_fts(documents_fts) VALUES ('rebuild')")
    conn.commit()