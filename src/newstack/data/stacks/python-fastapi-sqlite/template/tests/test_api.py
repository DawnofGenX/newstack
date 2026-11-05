"""One database per test, so the suite never touches the repository."""

from __future__ import annotations

import sqlite3

import pytest
from fastapi.testclient import TestClient

from {{ package_name }}.db import connect, migrate
from {{ package_name }}.main import create_app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "notes.db"))
    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture()
def database(tmp_path, monkeypatch):
    path = tmp_path / "notes.db"
    monkeypatch.setenv("DB_PATH", str(path))
    connection = connect(str(path))
    yield connection
    connection.close()


def test_health_counts_notes(client) -> None:
    assert client.get("/health").json() == {"status": "ok", "notes": 0}


def test_migrations_are_idempotent(database) -> None:
    first = migrate(database)
    assert first == ["001_notes.sql"], "the first run applies the only migration"
    schema_before = database.execute(
        "SELECT name, sql FROM sqlite_master ORDER BY name"
    ).fetchall()
    assert migrate(database) == [], "a second run must do nothing"
    schema_after = database.execute(
        "SELECT name, sql FROM sqlite_master ORDER BY name"
    ).fetchall()
    assert [tuple(row) for row in schema_before] == [tuple(row) for row in schema_after]
    assert database.execute("SELECT count(*) FROM schema_migrations").fetchone()[0] == 1


def test_create_returns_the_stored_note(client) -> None:
    response = client.post("/notes", json={"title": "shopping", "body": "milk"})
    assert response.status_code == 201
    note = response.json()
    assert note["id"] == 1
    assert note["title"] == "shopping"
    assert note["body"] == "milk"
    assert note["created_at"] == note["updated_at"]


def test_blank_title_is_rejected(client) -> None:
    assert client.post("/notes", json={"title": "   "}).status_code == 422
    assert client.post("/notes", json={}).status_code == 422


def test_body_defaults_to_empty(client) -> None:
    assert client.post("/notes", json={"title": "bare"}).json()["body"] == ""


def test_list_is_ordered_by_id(client) -> None:
    for title in ("one", "two", "three"):
        client.post("/notes", json={"title": title})
    notes = client.get("/notes").json()["notes"]
    assert [note["title"] for note in notes] == ["one", "two", "three"]


def test_missing_note_is_404_with_detail(client) -> None:
    response = client.get("/notes/99")
    assert response.status_code == 404
    assert response.json()["detail"] == {"error": "not_found", "detail": "no note with id 99"}


def test_patch_keeps_untouched_fields(client) -> None:
    created = client.post("/notes", json={"title": "draft", "body": "text"}).json()
    patched = client.patch(f"/notes/{created['id']}", json={"title": "final"})
    assert patched.status_code == 200
    note = patched.json()
    assert note["title"] == "final"
    assert note["body"] == "text"
    assert note["created_at"] == created["created_at"]


def test_delete_then_get_is_404(client) -> None:
    created = client.post("/notes", json={"title": "gone"}).json()
    assert client.delete(f"/notes/{created['id']}").status_code == 204
    assert client.get(f"/notes/{created['id']}").status_code == 404
    assert client.delete("/notes/4040").status_code == 404


def test_rows_survive_a_new_connection(client, tmp_path) -> None:
    client.post("/notes", json={"title": "durable"})
    fresh = connect(str(tmp_path / "notes.db"))
    try:
        titles = [row["title"] for row in fresh.execute("SELECT title FROM notes")]
    finally:
        fresh.close()
    assert titles == ["durable"], "the file, not the process, holds the data"


def test_schema_rejects_duplicate_migration_rows(database) -> None:
    migrate(database)
    with pytest.raises(sqlite3.IntegrityError):
        database.execute("INSERT INTO schema_migrations (name) VALUES ('001_notes.sql')")
