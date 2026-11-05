"""The console script: push, claim, complete, fail, drain, stats.

Exit codes are part of the contract, because a shell is the usual caller:

* 0 — the command did what it says
* 1 — nothing to do (no claimable job) or a gate the caller asked for
* 2 — the queue was asked to do something it refuses
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any

from . import selftest
from . import store as store_mod
from . import worker as worker_mod
from .store import DEAD, DEFAULT_LEASE_S, Job, LeaseLost, QueueError, Store

PROGRAM = "{{ npm_name }}"
VERSION = "0.1.0"
EXIT_OK = 0
EXIT_NOTHING = 1
EXIT_UNUSABLE = 2
DEFAULT_DB = Path("queue.db")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="A SQLite job queue with leases, retries and a dead-letter state.",
    )
    parser.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="queue database file")
    commands = parser.add_subparsers(dest="command", required=True)

    push = commands.add_parser("push", help="add a job")
    push.add_argument("payload", nargs="?", default="-", help="JSON object, @file, or - for stdin")
    push.add_argument("--queue", default=store_mod.DEFAULT_QUEUE)
    push.add_argument("--delay", type=float, default=0.0, help="seconds before it is claimable")
    push.add_argument("--max-attempts", type=int, default=store_mod.DEFAULT_MAX_ATTEMPTS)

    claim = commands.add_parser("claim", help="lease one job and print it as JSON")
    claim.add_argument("--worker", default="worker")
    claim.add_argument("--lease", type=float, default=DEFAULT_LEASE_S)

    complete = commands.add_parser("complete", help="mark a job done")
    complete.add_argument("job_id")
    complete.add_argument("--worker", default="worker")
    complete.add_argument("--result", default=None, help="JSON result to store")

    fail = commands.add_parser("fail", help="record a failed attempt")
    fail.add_argument("job_id")
    fail.add_argument("--worker", default="worker")
    fail.add_argument("--error", default="failed")

    listing = commands.add_parser("list", help="list jobs")
    listing.add_argument("--state", default=None)
    listing.add_argument("--queue", default=None)
    listing.add_argument("--json", action="store_true")

    commands.add_parser("stats", help="count jobs per state")

    drain = commands.add_parser("drain", help="work the queue until it is empty")
    drain.add_argument("--worker", default="drainer")
    drain.add_argument("--handler", default="noop", help="module:function to run per job")
    drain.add_argument("--max-jobs", type=int, default=None)
    drain.add_argument("--lease", type=float, default=DEFAULT_LEASE_S)
    drain.add_argument("--heartbeat", type=float, default=None)
    drain.add_argument("--json", action="store_true")

    commands.add_parser("selftest", help="run the offline checks")
    return parser


def _payload(text: str) -> dict[str, Any]:
    if text == "-":
        text = sys.stdin.read()
    elif text.startswith("@"):
        try:
            text = Path(text[1:]).read_text()
        except OSError as error:
            raise QueueError(f"cannot read {text[1:]}: {error.strerror or error}") from error
    try:
        value = json.loads(text)
    except json.JSONDecodeError as error:
        raise QueueError(f"payload is not JSON: {error}") from error
    if not isinstance(value, dict):
        raise QueueError("payload must be a JSON object")
    return value


def _handler(spec: str) -> worker_mod.Handler:
    if spec == "noop":
        return lambda job: {"ok": True, "job": job.id}
    module_name, _, function_name = spec.partition(":")
    if not module_name or not function_name:
        raise QueueError(f"--handler wants module:function, got {spec!r}")
    try:
        module = importlib.import_module(module_name)
    except ImportError as error:
        raise QueueError(f"cannot import {module_name}: {error}") from error
    function = getattr(module, function_name, None)
    if not callable(function):
        raise QueueError(f"{module_name} has no callable {function_name}")
    return function


def cmd_push(store: Store, args: argparse.Namespace) -> int:
    job_id = store.push(
        _payload(args.payload),
        queue=args.queue,
        delay_s=args.delay,
        max_attempts=args.max_attempts,
    )
    print(job_id)
    return EXIT_OK


def cmd_claim(store: Store, args: argparse.Namespace) -> int:
    job = store.claim(args.worker, lease_s=args.lease)
    if job is None:
        print("nothing to claim", file=sys.stderr)
        return EXIT_NOTHING
    print(json.dumps(_job_dict(job), indent=2))
    return EXIT_OK


def cmd_complete(store: Store, args: argparse.Namespace) -> int:
    result = None if args.result is None else json.loads(args.result)
    job = _job_from(store, args.job_id, args.worker)
    store.complete(job, args.worker, result)
    return EXIT_OK


def cmd_fail(store: Store, args: argparse.Namespace) -> int:
    job = _job_from(store, args.job_id, args.worker)
    state = store.fail(job, args.worker, args.error)
    print(state)
    return EXIT_OK if state != DEAD else EXIT_NOTHING


def cmd_list(store: Store, args: argparse.Namespace) -> int:
    jobs = store.list(state=args.state, queue=args.queue)
    if args.json:
        print(json.dumps(jobs, indent=2))
        return EXIT_OK
    for job in jobs:
        print(
            f"{job['id'][:12]}  {job['state']:<7} {job['queue']:<12} "
            f"attempts={job['attempts']}/{job['max_attempts']} {job['payload']}"
        )
    if not jobs:
        print("(no jobs)")
    return EXIT_OK


def cmd_stats(store: Store, args: argparse.Namespace) -> int:
    counts = store.stats()
    print("  ".join(f"{name}={counts[name]}" for name in store_mod.STATES))
    return EXIT_OK


def cmd_drain(store: Store, args: argparse.Namespace) -> int:
    report = worker_mod.drain(
        store,
        _handler(args.handler),
        worker=args.worker,
        max_jobs=args.max_jobs,
        lease_s=args.lease,
        heartbeat_s=args.heartbeat,
    )
    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
    else:
        print(
            f"drained {report.processed} done, {report.failed} retryable, "
            f"{report.dead} dead, {report.lost} lost"
        )
    return EXIT_OK


def _job_dict(job: Job) -> dict[str, Any]:
    return {
        "id": job.id,
        "queue": job.queue,
        "payload": job.payload,
        "attempts": job.attempts,
        "max_attempts": job.max_attempts,
    }


def _job_from(store: Store, job_id: str, worker: str) -> Job:
    record = store.get(job_id)
    if record["worker"] != worker or record["state"] != store_mod.LEASED:
        raise LeaseLost(f"job {job_id} is not leased by {worker}")
    return Job(
        id=record["id"],
        queue=record["queue"],
        payload=record["payload"],
        attempts=record["attempts"],
        max_attempts=record["max_attempts"],
    )


HANDLERS = {
    "push": cmd_push,
    "claim": cmd_claim,
    "complete": cmd_complete,
    "fail": cmd_fail,
    "list": cmd_list,
    "stats": cmd_stats,
    "drain": cmd_drain,
}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "selftest":
        return selftest.main()
    try:
        with Store(args.db) as store:
            return HANDLERS[args.command](store, args)
    except (QueueError, LeaseLost) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return EXIT_UNUSABLE
    except json.JSONDecodeError as error:
        print(f"{PROGRAM}: not JSON: {error}", file=sys.stderr)
        return EXIT_UNUSABLE


if __name__ == "__main__":
    raise SystemExit(main())
