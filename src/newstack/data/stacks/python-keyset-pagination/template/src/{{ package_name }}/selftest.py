"""Self-checks: the cursor round trip, the walk, and the two mutations that matter."""

from __future__ import annotations

import base64
import json
import tempfile
from pathlib import Path

from .demo import run as run_demo
from .model import Cursor, InputError, Order, Query
from .pager import scan, walk
from .store import Store, StoreError


class Checks:
    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0

    def ok(self, description: str, condition: bool) -> None:
        if condition:
            self.passed += 1
            print(f"ok    {description}")
        else:
            self.failed += 1
            print(f"FAIL  {description}")

    def equal(self, description: str, want: object, got: object) -> None:
        if want == got:
            self.passed += 1
            print(f"ok    {description}")
        else:
            self.failed += 1
            print(f"FAIL  {description}: wanted {want!r}, got {got!r}")

    def raises(self, description: str, function, *args, **kwargs) -> None:
        try:
            function(*args, **kwargs)
        except (InputError, ValueError, TypeError, StoreError):
            self.passed += 1
            print(f"ok    {description}")
        else:
            self.failed += 1
            print(f"FAIL  {description}: no error raised")


def _order_checks(checks: Checks) -> None:
    checks.equal(
        "an ascending order sorts by key then id", "created_at ASC, id ASC", Order().columns()
    )
    checks.equal(
        "a descending order sorts both columns backwards",
        "title DESC, id DESC",
        Order("title", True).columns(),
    )
    checks.equal("the arrow matches the direction", "desc", Order("created_at", True).arrow)
    checks.equal(
        "the comparison follows the direction",
        "(created_at, id) < (?, ?)",
        Order("created_at", True).comparison(),
    )
    checks.raises("an unknown sort key is refused", Order, "body")


def _cursor_checks(checks: Checks) -> None:
    query = Query(Order("created_at", False), "note")
    cursor = Cursor(1_700_000_004, 12, query.fingerprint)
    text = cursor.encode()
    checks.ok("the cursor is base64url without padding", "=" not in text)
    checks.ok(
        "the cursor decodes to what went in",
        Cursor.decode(text) == cursor,
    )
    checks.ok("the cursor is not readable as plain json", "sort" not in text)
    checks.equal("a matching query passes the check", None, cursor.check(query))
    checks.raises(
        "a cursor from another query is refused",
        cursor.check,
        Query(Order("created_at", False), "other"),
    )
    checks.raises("a non-base64 cursor is refused", Cursor.decode, "not base64 !!!")
    checks.raises("an empty cursor is refused", Cursor.decode, "")
    checks.raises(
        "a cursor with a missing member is refused",
        Cursor.decode,
        base64.urlsafe_b64encode(b'{"sort":1}').decode().rstrip("="),
    )
    checks.raises(
        "a cursor with a non-integer id is refused",
        Cursor.decode,
        base64.urlsafe_b64encode(b'{"sort":1,"id":"x","query":"abc"}').decode().rstrip("="),
    )
    checks.raises(
        "a cursor from a future version is refused",
        Cursor.decode,
        base64.urlsafe_b64encode(b'{"v":9,"sort":1,"id":1,"query":"abc"}').decode().rstrip("="),
    )
    payload = json.dumps({"sort": 1, "id": 1, "query": "abc"}).encode()
    checks.ok(
        "a cursor without a version is accepted as version 1",
        Cursor.decode(base64.urlsafe_b64encode(payload).decode().rstrip("=")).ident == 1,
    )


def _store_checks(checks: Checks, directory: Path) -> None:
    with Store(directory / "store.db") as store:
        store.seed(30)
        checks.equal("the seed creates the count it was asked for", 30, store.count())
        ids = store.ordered_ids(Query())
        checks.equal("the ordered ids are as many as the rows", 30, len(ids))
        first = store.fetch(Query(), size=7)[0]
        checks.equal("a page is the size it was asked for", 7, len(first))
        checks.ok("a full page knows there is more", store.fetch(Query(), size=7)[1])
        checks.equal(
            "the order is the key then the id",
            ids[:7],
            [row.id for row in first],
        )
        titled = store.fetch(Query(Order("title")), size=100)[0]
        pairs = [(row.title, row.id) for row in titled]
        checks.ok("ordering by title sorts by the title", pairs == sorted(pairs))
        prefix = Query(title_prefix="note 01")
        checks.equal("a prefix filter narrows the population", 10, store.count(prefix))
        checks.raises("an oversized page is refused", store.fetch, Query(), size=10_000)
        checks.raises("a zero page is refused", store.fetch, Query(), size=0)
        store.delete(ids[0])
        checks.equal("a deletion is a deletion", 29, store.count())


def _walk_checks(checks: Checks, directory: Path) -> None:
    with Store(directory / "walk.db") as store:
        store.seed(30)
        expected = store.ordered_ids(Query())
        checks.equal("a scan sees every row exactly once", expected, scan(store, Query(), size=7))
        checks.equal("a scan with a big page agrees", expected, scan(store, Query(), size=100))
        checks.equal(
            "a scan by title agrees with the database",
            store.ordered_ids(Query(Order("title"))),
            scan(store, Query(Order("title")), size=4),
        )
        first = scan(store, Query(), size=7)
        checks.equal(
            "a scan from a cursor continues the walk", first, walk(store, Query(), size=100)
        )
        descending = Query(Order("created_at", True))
        checks.equal(
            "a descending scan is the reverse of the ascending one",
            list(reversed(expected)),
            scan(store, descending, size=5),
        )


def _demo_checks(checks: Checks, directory: Path) -> None:
    steps = run_demo(directory / "demo")
    checks.equal("the demo runs two scenarios", 2, len(steps))
    for step in steps:
        checks.ok(f"the cursor walk survives {step.scenario!r}", step.keyset_clean)
        checks.ok(f"the offset walk breaks on {step.scenario!r}", step.offset_broken)
    checks.ok(
        "the deletion scenario costs the offset walk a row",
        steps[0].offset_skipped >= 1,
    )
    checks.ok(
        "the insertion scenario costs the offset walk a repeat",
        steps[1].offset_duplicated >= 1,
    )


def run() -> int:
    checks = Checks()
    with tempfile.TemporaryDirectory() as raw:
        directory = Path(raw)
        (directory / "demo").mkdir()
        _order_checks(checks)
        _cursor_checks(checks)
        _store_checks(checks, directory)
        _walk_checks(checks, directory)
        _demo_checks(checks, directory)
    total = checks.passed + checks.failed
    print(f"selftest: {checks.passed} checks passed, {checks.failed} failed out of {total}")
    return 0 if checks.failed == 0 else 1
