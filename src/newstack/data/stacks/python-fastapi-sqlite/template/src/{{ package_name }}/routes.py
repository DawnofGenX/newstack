"""Routes: notes CRUD over one SQLite file, no ORM in the way."""

from __future__ import annotations

import sqlite3
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field, field_validator

from .db import connection_scope

router = APIRouter()

Connection = Annotated[sqlite3.Connection, Depends(connection_scope)]


class NoteIn(BaseModel):
    title: str = Field(min_length=1)
    body: str = ""

    @field_validator("title")
    @classmethod
    def title_must_have_content(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("title must not be blank")
        return value.strip()


class NotePatch(BaseModel):
    title: str | None = None
    body: str | None = None

    @field_validator("title")
    @classmethod
    def title_must_have_content(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("title must not be blank")
        return value.strip() if value is not None else None


def _row_to_note(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "title": row["title"],
        "body": row["body"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _fetch(connection: sqlite3.Connection, note_id: int) -> dict[str, Any]:
    row = connection.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found", "detail": f"no note with id {note_id}"},
        )
    return _row_to_note(row)


@router.get("/health")
def health(connection: Connection) -> dict[str, Any]:
    total = connection.execute("SELECT count(*) AS n FROM notes").fetchone()["n"]
    return {"status": "ok", "notes": total}


@router.get("/notes")
def list_notes(connection: Connection) -> dict[str, Any]:
    rows = connection.execute("SELECT * FROM notes ORDER BY id").fetchall()
    return {"notes": [_row_to_note(row) for row in rows]}


@router.post("/notes", status_code=status.HTTP_201_CREATED)
def create_note(payload: NoteIn, connection: Connection) -> dict[str, Any]:
    with connection:
        cursor = connection.execute(
            "INSERT INTO notes (title, body) VALUES (?, ?)", (payload.title, payload.body)
        )
    return _fetch(connection, int(cursor.lastrowid))


@router.get("/notes/{note_id}")
def get_note(note_id: int, connection: Connection) -> dict[str, Any]:
    return _fetch(connection, note_id)


@router.patch("/notes/{note_id}")
def patch_note(note_id: int, payload: NotePatch, connection: Connection) -> dict[str, Any]:
    current = _fetch(connection, note_id)
    title = payload.title if payload.title is not None else current["title"]
    body = payload.body if payload.body is not None else current["body"]
    with connection:
        connection.execute(
            "UPDATE notes SET title = ?, body = ?,"
            " updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = ?",
            (title, body, note_id),
        )
    return _fetch(connection, note_id)


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: int, connection: Connection) -> Response:
    _fetch(connection, note_id)
    with connection:
        connection.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
