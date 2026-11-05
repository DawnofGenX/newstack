"""Every claim the README makes, executed: the hash rules, the chain, and the three attacks."""

from __future__ import annotations

import tempfile
from collections.abc import Callable
from pathlib import Path

from . import demo
from .canon import CanonError, canonical, digest
from .record import GENESIS, body_of, event_of
from .store import Store
from .verify import checkpoint_of, verify


class Checks:
    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0

    def ok(self, name: str, condition: bool) -> None:
        if condition:
            self.passed += 1
            print(f"ok   {name}")
        else:
            self.failed += 1
            print(f"FAIL {name}")

    def equal(self, name: str, want: object, got: object) -> None:
        self.ok(f"{name} (want {want!r}, got {got!r})", want == got)

    def raises(self, name: str, error: type[BaseException], action: Callable[[], object]) -> None:
        try:
            action()
        except error:
            self.ok(name, True)
        except BaseException as unexpected:
            self.ok(f"{name} (raised {type(unexpected).__name__} instead)", False)
        else:
            self.ok(f"{name} (nothing was raised)", False)


def _canon_checks(checks: Checks) -> None:
    checks.equal("keys are sorted", '{"a":1,"b":2}', canonical({"b": 2, "a": 1}))
    checks.equal("there is no incidental whitespace", '{"a":[1,2]}', canonical({"a": [1, 2]}))
    checks.equal("unicode is kept as UTF-8", '{"note":"café"}', canonical({"note": "café"}))
    checks.equal(
        "the digest ignores key order",
        digest({"a": 1, "b": 2}),
        digest({"b": 2, "a": 1}),
    )
    checks.ok("the digest is 64 hex characters", len(digest({"a": 1})) == 64)
    checks.raises(
        "a float is refused",
        CanonError,
        lambda: canonical({"ratio": 0.5}),
    )
    checks.raises("a set is refused", CanonError, lambda: canonical({"tags": {1, 2}}))
    checks.raises("a non-string key is refused", CanonError, lambda: canonical({1: "one"}))
    checks.raises(
        "a nested float is refused too",
        CanonError,
        lambda: canonical({"rows": [{"ratio": 1.5}]}),
    )


def _record_checks(checks: Checks) -> None:
    body = body_of(1, "alice", "note.update", "note/1", detail={"field": "title"})
    event = event_of(body)
    checks.equal("the first event links to genesis", GENESIS, body["prev_hash"])
    checks.ok("the hash covers the body but is not in it", "hash" not in event.body)
    checks.ok("the hash is recomputed from the body", event.hash == event_of(body).hash)
    checks.raises("an empty actor is refused", ValueError, lambda: body_of(1, "", "a", "t"))
    checks.raises("seq 0 is refused", ValueError, lambda: body_of(0, "a", "a", "t"))
    checks.raises(
        "a local timestamp is refused",
        ValueError,
        lambda: body_of(1, "a", "a", "t", at="2026-11-05T10:00:00"),
    )
    checks.raises(
        "a float in the detail is refused at append time",
        ValueError,
        lambda: body_of(1, "a", "a", "t", detail={"ratio": 0.5}),
    )


def _store_checks(checks: Checks) -> None:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "log.db"
        with Store(path) as store:
            first = store.append(actor="alice", action="note.update", target="note/1")
            second = store.append(actor="bob", action="note.delete", target="note/2")
            checks.equal("the first event is seq 1", 1, first.seq)
            checks.equal("the second is seq 2", 2, second.seq)
            checks.equal("the second links to the first", first.hash, second.prev_hash)
            checks.equal("the head is the last event", second.hash, store.head().hash)
            checks.equal("the count is the number of rows", 2, store.count())
            checks.equal(
                "the first event is readable by sequence number", first.hash, store.get(1).hash
            )
            checks.equal("a limit truncates the read", 1, len(store.events(limit=1)))
            checks.equal("a start skips the earlier rows", 1, len(store.events(start=2)))
        with Store(path) as reopened:
            checks.equal("the chain survives a reopen", 2, reopened.head().seq)
            checks.equal("reopening does not append", 2, reopened.count())


def _verify_checks(checks: Checks) -> None:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "log.db"
        with Store(path) as store:
            for index in range(1, 4):
                store.append(actor="alice", action="note.update", target=f"note/{index}")
            checks.ok("a clean log verifies", verify(store).ok)
            checkpoint = checkpoint_of(store)
            checks.equal("the checkpoint counts the events", 3, checkpoint.count)
            checks.equal("and remembers the head", 3, checkpoint.seq)

            demo.edit_body(store, 2, {"note": "I was never here"})
            report = verify(store)
            checks.ok("an edited body is caught", not report.ok)
            checks.equal("and named as a body change", "body-changed", report.problems[0].kind)

            store.append(actor="alice", action="note.update", target="note/4")
            # An edited body is caught at its own row and nowhere else: the stored hash column
            # never changed, so the next event still links to it. A chain proves links, not prose.
            kinds = [problem.kind for problem in verify(store).problems]
            checks.equal("the edit is still the only problem", 1, len(kinds))
            checks.ok("and it is not reported as a broken link", "chain-broken" not in kinds)

            # A head checkpoint remembers the count and the head hash. An edit below the head and a
            # later append are both outside what it can see — the chain above is what catches them.
            guarded = verify(store, checkpoint)
            checks.equal(
                "a head checkpoint adds nothing of its own below the head", 1, len(guarded.problems)
            )

            demo.delete_event(store, 3)
            kinds = [problem.kind for problem in verify(store).problems]
            checks.ok("a deleted row is caught as a gap", "gap" in kinds)
            rewritten = verify(store, checkpoint)
            checks.ok(
                "and the checkpoint notices the row it remembered is gone",
                any(problem.kind == "rewritten" for problem in rewritten.problems),
            )

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "short.db"
        with Store(path) as store:
            for index in range(1, 4):
                store.append(actor="alice", action="note.update", target=f"note/{index}")
            checkpoint = checkpoint_of(store)
            demo.delete_event(store, 3)
            truncated = verify(store, checkpoint)
            checks.ok(
                "a checkpoint notices the log got shorter",
                any(problem.kind == "truncated" for problem in truncated.problems),
            )

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "log.db"
        with Store(path) as store:
            for index in range(1, 4):
                store.append(actor="alice", action="note.update", target=f"note/{index}")
            checkpoint = checkpoint_of(store)
            store.append(actor="alice", action="note.update", target="note/4")
            checks.ok("growing after a checkpoint is not a failure", verify(store, checkpoint).ok)
            demo.rebuild_chain(store)
            chain_only = verify(store)
            checks.ok("a full rewrite passes the chain alone", chain_only.ok)
            guarded = verify(store, checkpoint)
            checks.ok("and fails against the checkpoint", not guarded.ok)
            checks.equal("the checkpoint names the rewrite", "rewritten", guarded.problems[0].kind)


def _demo_checks(checks: Checks) -> None:
    with tempfile.TemporaryDirectory() as directory:
        steps = demo.run(Path(directory))
    checks.equal("the demo runs five scenarios", 5, len(steps))
    checks.ok("the clean log is not an attack", steps[0].caught)
    checks.ok("the edit is caught", steps[1].caught)
    checks.ok("the deletion is caught", steps[2].caught)
    checks.ok("the rewrite is NOT caught by the chain", not steps[3].caught)
    checks.ok("the rewrite IS caught by the checkpoint", steps[4].caught)


def run() -> int:
    checks = Checks()
    for group in (_canon_checks, _record_checks, _store_checks, _verify_checks, _demo_checks):
        group(checks)
    total = checks.passed + checks.failed
    print(f"\nselftest: {checks.passed} checks passed, {checks.failed} failed out of {total}")
    return 0 if checks.failed == 0 else 1
