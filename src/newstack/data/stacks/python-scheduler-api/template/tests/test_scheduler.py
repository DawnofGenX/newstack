"""The scheduler's promises, tested against a real database and a real ticker."""

from __future__ import annotations

import sqlite3
import time

import pytest
from fastapi.testclient import TestClient

from {{ package_name }} import db, jobs
from {{ package_name }}.main import create_app
from {{ package_name }}.worker import Scheduler


@pytest.fixture()
def store(tmp_path):
    path = tmp_path / "scheduler.db"
    connection = db.connect(path)
    db.migrate(connection)
    try:
        yield path, connection
    finally:
        connection.close()


@pytest.fixture()
def client(tmp_path):
    app = create_app(tmp_path / "api.db", tick=0.02)
    with TestClient(app) as running:
        yield running


def wait_for(predicate, timeout: float = 5.0, interval: float = 0.02):
    deadline = time.time() + timeout
    while time.time() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(interval)
    raise AssertionError("condition never became true")


def test_migrations_are_idempotent(store):
    _path, connection = store
    assert db.migrate(connection) == []
    tables = {
        row["name"]
        for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    }
    assert {"jobs", "runs", "schema_migrations"} <= tables


def test_counts_are_wc_counts(store):
    assert jobs.count_text("héllo wörld\n") == {"lines": 1, "words": 2, "bytes": 14}
    assert jobs.count_text("a b\nc\n") == {"lines": 2, "words": 3, "bytes": 6}
    assert jobs.count_text("") == {"lines": 0, "words": 0, "bytes": 0}


def test_a_due_job_runs_once_and_is_done(store):
    path, connection = store
    job = jobs.create(connection, name="once", kind="count", payload="a b\n", run_at=1000.0, at=1000.0)
    scheduler = Scheduler(path, tick=0.02, clock=lambda: 1000.0)
    assert scheduler.drain() == 1
    after = jobs.fetch(connection, job["id"])
    assert after["status"] == "done"
    assert after["attempts"] == 0
    rows = jobs.runs(connection, job["id"])
    assert len(rows) == 1
    assert (rows[0]["lines"], rows[0]["words"], rows[0]["bytes"]) == (1, 2, 4)
    assert scheduler.drain() == 0, "a job that already ran is not due again"


def test_an_interval_job_reschedules_into_the_future(store):
    path, connection = store
    job = jobs.create(
        connection, name="tick", run_at=1000.0, interval_seconds=0.5, at=1000.0
    )
    scheduler = Scheduler(path, tick=0.02, clock=lambda: 1000.0)
    scheduler.drain()
    after = jobs.fetch(connection, job["id"])
    assert after["status"] == "pending"
    assert after["run_at"] == pytest.approx(1000.5)
    assert jobs.runs(connection, job["id"])[0]["status"] == "ok"


def test_an_overdue_job_catches_up_once_not_once_per_interval(store):
    path, connection = store
    job = jobs.create(
        connection,
        name="late",
        run_at=900.0,
        interval_seconds=10.0,
        at=900.0,
    )
    scheduler = Scheduler(path, tick=0.02, clock=lambda: 1000.0)
    assert scheduler.drain() == 1
    after = jobs.fetch(connection, job["id"])
    assert after["status"] == "pending"
    assert after["run_at"] == pytest.approx(1010.0), "one run, next slot in the future"
    assert len(jobs.runs(connection, job["id"])) == 1


def test_a_failing_job_backs_off_then_gives_up(store):
    path, connection = store
    job = jobs.create(
        connection, name="boom", kind="explode", run_at=1000.0, max_attempts=2, at=1000.0
    )
    clock = {"at": 1000.0}
    scheduler = Scheduler(path, tick=0.02, clock=lambda: clock["at"])

    scheduler.drain()
    first = jobs.fetch(connection, job["id"])
    assert (first["status"], first["attempts"]) == ("pending", 1)
    assert first["run_at"] == pytest.approx(1000.0 + jobs.backoff(1))
    assert "RuntimeError" in first["last_error"]

    clock["at"] = first["run_at"]
    scheduler.drain()
    second = jobs.fetch(connection, job["id"])
    assert (second["status"], second["attempts"]) == ("failed", 2)
    assert len(jobs.runs(connection, job["id"])) == 2
    assert jobs.runs(connection, job["id"])[-1]["status"] == "error"


def test_two_tickers_never_run_the_same_job_twice(store):
    """The claim is the serialisation point, not the loop."""
    path, connection = store
    ids = [
        jobs.create(connection, name=f"job-{n}", run_at=1000.0, at=1000.0)["id"] for n in range(6)
    ]
    first = Scheduler(path, tick=0.02, clock=lambda: 1000.0)
    second = Scheduler(path, tick=0.02, clock=lambda: 1000.0)
    first.start()
    second.start()
    try:
        wait_for(lambda: all(jobs.fetch(connection, i)["status"] == "done" for i in ids))
    finally:
        first.stop()
        second.stop()
    for job_id in ids:
        assert len(jobs.runs(connection, job_id)) == 1


def test_a_claim_takes_a_write_lock(store):
    _path, connection = store
    job = jobs.create(connection, name="locked", run_at=1000.0, at=1000.0)
    claimed = jobs.claim(connection, at=1000.0)
    assert [row["id"] for row in claimed] == [job["id"]]
    assert claimed[0]["locked_until"] == pytest.approx(1000.0 + jobs.LEASE_SECONDS)
    assert jobs.claim(connection, at=1000.0) == [], "a second claim inside the lease sees nothing"


def test_health_reports_jobs_and_due(client):
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["jobs"] == 0
    client.post("/jobs", json={"name": "now", "payload": "a b", "run_at": 0})
    client.get("/health")
    wait_for(lambda: client.get("/health").json()["jobs"] == 1)
    assert client.get("/health").json()["due"] >= 0


def test_create_and_list_jobs(client):
    created = client.post(
        "/jobs", json={"name": "  digest  ", "payload": "a\n", "interval_seconds": 3600}
    )
    assert created.status_code == 201
    job = created.json()
    assert job["name"] == "digest"
    assert job["status"] == "pending"
    assert job["interval_seconds"] == 3600
    assert job["run_at"] > 0

    listing = client.get("/jobs").json()
    assert listing["count"] == 1
    assert listing["jobs"][0]["id"] == job["id"]
    assert client.get("/jobs", params={"status": "done"}).json()["count"] == 0


def test_validation_is_an_envelope_not_a_traceback(client):
    blank = client.post("/jobs", json={"name": "   "})
    assert blank.status_code == 422
    assert blank.json()["error"] == "invalid_request"

    kind = client.post("/jobs", json={"name": "x", "kind": "shell"})
    assert kind.status_code == 422
    assert kind.json()["error"] == "invalid_request"

    interval = client.post("/jobs", json={"name": "x", "interval_seconds": 0})
    assert interval.status_code == 422
    assert "interval_seconds" in interval.json()["detail"]


def test_run_now_hands_the_job_to_the_ticker(client):
    job = client.post("/jobs", json={"name": "later", "payload": "a b\nc\n", "run_at": time.time() + 3600}).json()
    assert client.post(f"/jobs/{job['id']}/run").json()["run_at"] <= time.time()

    wait_for(lambda: client.get(f"/jobs/{job['id']}").json()["status"] == "done")
    history = client.get(f"/jobs/{job['id']}/runs").json()
    assert history["count"] == 1
    assert history["runs"][0]["words"] == 3


def test_interval_job_keeps_running_under_the_ticker(client):
    job = client.post("/jobs", json={"name": "beat", "payload": "a\n", "interval_seconds": 0.05}).json()
    wait_for(lambda: client.get(f"/jobs/{job['id']}/runs").json()["count"] >= 2)
    body = client.get(f"/jobs/{job['id']}").json()
    assert body["status"] == "pending"
    assert body["attempts"] == 0


def test_a_broken_job_ends_up_failed(client):
    job = client.post(
        "/jobs", json={"name": "boom", "kind": "explode", "max_attempts": 2}
    ).json()
    wait_for(lambda: client.get(f"/jobs/{job['id']}").json()["status"] == "failed")
    body = client.get(f"/jobs/{job['id']}").json()
    assert body["attempts"] == 2
    assert "error" == client.get(f"/jobs/{job['id']}/runs").json()["runs"][-1]["status"]


def test_delete_takes_the_history_with_it(client):
    job = client.post("/jobs", json={"name": "gone"}).json()
    client.post(f"/jobs/{job['id']}/run")
    wait_for(lambda: client.get(f"/jobs/{job['id']}").json()["status"] == "done")
    assert client.delete(f"/jobs/{job['id']}").status_code == 204
    assert client.delete(f"/jobs/{job['id']}").status_code == 404
    missing = client.get(f"/jobs/{job['id']}").json()
    assert missing == {"error": "not_found", "detail": f"no job with id {job['id']}"}


def test_unknown_routes_and_methods_share_one_envelope(client):
    missing = client.get("/nope")
    assert missing.status_code == 404
    assert missing.json()["error"] == "not_found"
    assert missing.json()["detail"] == "no route for GET /nope"

    wrong = client.request("PATCH", "/health")
    assert wrong.status_code == 405
    assert wrong.json()["error"] == "method_not_allowed"


def test_jobs_survive_a_restart(tmp_path):
    path = tmp_path / "restart.db"
    connection = db.connect(path)
    db.migrate(connection)
    job = jobs.create(connection, name="keep", payload="a b\n", run_at=2000.0, at=1000.0)
    connection.close()

    second = Scheduler(path, tick=0.02, clock=lambda: 2000.0)
    second.drain()
    check = db.connect(path)
    try:
        after = jobs.fetch(check, job["id"])
        assert after["status"] == "done"
        assert jobs.runs(check, job["id"])[0]["bytes"] == 4
    finally:
        check.close()


def test_a_foreign_key_cascade_is_on(store):
    _path, connection = store
    job = jobs.create(connection, name="x", run_at=1000.0, at=1000.0)
    jobs.execute(connection, job, at=1000.0)
    connection.execute("DELETE FROM jobs WHERE id = ?", (job["id"],))
    left = connection.execute("SELECT COUNT(*) AS n FROM runs").fetchone()["n"]
    assert left == 0, "PRAGMA foreign_keys is per connection; without it rows leak"
    assert sqlite3.sqlite_version_info >= (3, 35), "the schema needs a modern sqlite"
