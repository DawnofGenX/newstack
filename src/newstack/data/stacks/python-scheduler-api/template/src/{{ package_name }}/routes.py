"""HTTP surface: create, inspect, run now, delete."""

from __future__ import annotations

import sqlite3
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field, field_validator

from . import db, jobs

router = APIRouter()


class JobIn(BaseModel):
    name: str
    kind: Literal["count", "explode"] = "count"
    payload: str = ""
    run_at: float | None = None
    interval_seconds: float | None = Field(default=None, gt=0)
    max_attempts: int = Field(default=3, ge=1, le=10)

    @field_validator("name")
    @classmethod
    def _named(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("name must not be blank")
        return value.strip()


def _connection(request: Request) -> Any:
    # `db.connect` is not a convenience: sqlite3's default isolation level opens
    # an implicit transaction, and closing a connection without committing throws
    # the write away. Handing the request a fresh `sqlite3.Connection(path)` reads
    # fine and silently loses every INSERT — the 201 still comes back.
    connection = db.connect(request.app.state.db_path)
    try:
        yield connection
    finally:
        connection.close()


Connection = Annotated[sqlite3.Connection, Depends(_connection)]


def _not_found(job_id: str) -> HTTPException:
    return HTTPException(
        status_code=404, detail={"error": "not_found", "detail": f"no job with id {job_id}"}
    )


def _clock(request: Request) -> float:
    return request.app.state.clock()


@router.get("/health")
def health(request: Request, connection: Connection) -> dict[str, Any]:
    return {
        "status": "ok",
        "jobs": connection.execute("SELECT COUNT(*) AS n FROM jobs").fetchone()["n"],
        "due": jobs.due_count(connection, _clock(request)),
    }


@router.get("/jobs")
def list_jobs(connection: Connection, status: str | None = None) -> dict[str, Any]:
    rows = jobs.listing(connection, status)
    return {"jobs": rows, "count": len(rows)}


@router.post("/jobs", status_code=201)
def create_job(
    payload: JobIn,
    request: Request,
    connection: Connection,
) -> dict[str, Any]:
    at = _clock(request)
    try:
        return jobs.create(
            connection,
            name=payload.name,
            kind=payload.kind,
            payload=payload.payload,
            run_at=at if payload.run_at is None else payload.run_at,
            interval_seconds=payload.interval_seconds,
            max_attempts=payload.max_attempts,
            at=at,
        )
    except jobs.JobError as exc:
        raise HTTPException(
            status_code=422, detail={"error": "invalid_job", "detail": str(exc)}
        ) from exc


@router.get("/jobs/{job_id}")
def get_job(job_id: str, connection: Connection) -> dict[str, Any]:
    job = jobs.fetch(connection, job_id)
    if job is None:
        raise _not_found(job_id)
    return job


@router.get("/jobs/{job_id}/runs")
def get_runs(job_id: str, connection: Connection) -> dict[str, Any]:
    if jobs.fetch(connection, job_id) is None:
        raise _not_found(job_id)
    rows = jobs.runs(connection, job_id)
    return {"runs": rows, "count": len(rows)}


@router.post("/jobs/{job_id}/run")
def run_now(
    job_id: str, request: Request, connection: Connection
) -> dict[str, Any]:
    """Make the job due right now; the ticker still owns the running."""
    job = jobs.fetch(connection, job_id)
    if job is None:
        raise _not_found(job_id)
    at = _clock(request)
    connection.execute(
        "UPDATE jobs SET run_at = ?, updated_at = ? WHERE id = ?", (at, at, job_id)
    )
    return jobs.fetch(connection, job_id) or {}


@router.delete("/jobs/{job_id}", status_code=204)
def delete_job(job_id: str, connection: Connection) -> Response:
    job = jobs.fetch(connection, job_id)
    if job is None:
        raise _not_found(job_id)
    connection.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    return Response(status_code=204)
