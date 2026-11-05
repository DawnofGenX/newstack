"""Prove the runner's rules against a real journal, in a temporary directory."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from . import demo, journal
from .runner import COMPLETED, INCOMPLETE, ROLLED_BACK, Saga, SagaError, Step

_results: list[tuple[bool, str, str]] = []


def check(name: str, condition: Any, detail: str = "") -> None:
    _results.append((bool(condition), name, detail))


def refuses(name: str, call: Any, kind: type[BaseException]) -> None:
    try:
        call()
    except kind as error:
        check(name, True, str(error)[:70])
    except BaseException as error:
        check(name, False, f"raised {type(error).__name__}, wanted {kind.__name__}")
    else:
        check(name, False, f"did not raise {kind.__name__}")


def _outcome(journal_path: Path, **kwargs: Any) -> Any:
    return demo.build(journal_path, **kwargs).run()


def _run(directory: Path) -> None:
    happy = _outcome(directory / "happy.jsonl", decline_at="")
    check("a clean run completes", happy.status == COMPLETED, happy.status)
    check("a clean run leaves every step succeeded", set(happy.statuses.values()) == {"succeeded"})
    check("a clean run makes three calls", happy.records >= 7, str(happy.records))

    declined = _outcome(directory / "declined.jsonl", decline_at="book-flight")
    check("a declined step rolls the saga back", declined.status == ROLLED_BACK, declined.status)
    check(
        "the failing step is named",
        declined.failed_step == "book-flight",
        str(declined.failed_step),
    )
    check("the failed step is not compensated", declined.statuses["book-flight"] == "failed")
    check("the charge was refunded", declined.statuses["charge-card"] == "compensated")
    check("the hotel was released", declined.statuses["reserve-hotel"] == "compensated")

    calls = demo.Calls()
    build_calls = demo.build(directory / "order.jsonl", calls=calls, decline_at="book-flight")
    build_calls.run()
    order = calls.names
    check(
        "compensations run in reverse order",
        order == ["reserve-hotel", "charge-card", "book-flight", "refund-card", "release-hotel"],
        " -> ".join(order),
    )
    check("nothing was compensated twice", order.count("refund-card") == 1)

    stuck = _outcome(
        directory / "stuck.jsonl", decline_at="book-flight", break_compensation="charge-card"
    )
    check(
        "a broken compensation makes the rollback incomplete",
        stuck.status == INCOMPLETE,
        stuck.status,
    )
    check("the broken step is reported", stuck.statuses["charge-card"] == "compensation_failed")
    check(
        "the remaining compensation still ran",
        stuck.statuses["reserve-hotel"] == "compensated",
        str(stuck.statuses),
    )
    check(
        "the outcome names what is left standing",
        any("charge-card" in n for n in stuck.unrecoverable),
    )

    flaky = demo.build(
        directory / "flaky.jsonl", decline_at="book-flight", flaky_compensation="charge-card"
    )
    flaky_outcome = flaky.run()
    check(
        "a compensation that fails once is retried",
        flaky_outcome.status == ROLLED_BACK,
        flaky_outcome.status,
    )
    check("the retried refund succeeded", flaky.state["calls"].refunds == 1)
    records = journal.read(directory / "flaky.jsonl")
    failed_refunds = [r for r in records if r["event"] == "step.compensation_failed"]
    check("the first refund attempt is in the journal", len(failed_refunds) == 1)

    irreversible = Saga(
        "no-undo",
        [
            Step("send-email", lambda context: context.key),
            Step("charge-card", lambda context: 1 / 0),
            Step("book", lambda context: None),
        ],
        directory / "irreversible.jsonl",
    )
    outcome = irreversible.run()
    check(
        "an irreversible step makes the rollback incomplete",
        outcome.status == INCOMPLETE,
        outcome.status,
    )
    check("the irreversible step is named", "send-email" in " ".join(outcome.unrecoverable))

    attempts: list[int] = []

    def transient(context: Any) -> None:
        attempts.append(context.attempt)
        if context.attempt == 1:
            raise TimeoutError("the first attempt timed out")

    retried = Saga(
        "retry-once",
        [Step("flaky", transient, max_attempts=2, retry_on=(TimeoutError,))],
        directory / "retry.jsonl",
    )
    check("a transient failure is retried", retried.run().status == COMPLETED)
    check("the retry used a second attempt", attempts == [1, 2], str(attempts))

    unretryable: list[int] = []

    def wrong_error(context: Any) -> None:
        unretryable.append(context.attempt)
        raise ValueError("this is not transient")

    refused_retry = Saga(
        "retry-filter",
        [Step("strict", wrong_error, max_attempts=3, retry_on=(TimeoutError,))],
        directory / "filter.jsonl",
    )
    check("retry_on stops the retries it does not name", refused_retry.run().status == ROLLED_BACK)
    check("only one attempt was made", unretryable == [1], str(unretryable))

    keys = [
        record["key"]
        for record in journal.read(directory / "retry.jsonl")
        if record["event"] == "step.started"
    ]
    check("every attempt carries the same idempotency key", len(set(keys)) == 1, str(keys))

    # A crash between "started" and any outcome: the step is retried, not assumed.
    crash_journal = directory / "crash.jsonl"
    journal.Journal(crash_journal).append(
        "crashed", "step.started", step="reserve-hotel", key="crashed:reserve-hotel", attempt=1
    )
    crashed = demo.build(crash_journal, saga_id="crashed", decline_at="")
    crash_outcome = crashed.run()
    check("an interrupted step is retried", crash_outcome.status == COMPLETED, crash_outcome.status)
    check(
        "the retry is recorded",
        any(record["event"] == "step.retried" for record in journal.read(crash_journal)),
    )
    check("the resumed run says so", crash_outcome.resumed)

    done = demo.build(directory / "happy.jsonl", decline_at="")
    again = done.run()
    check(
        "re-running a finished saga is a no-op",
        again.status == COMPLETED and not done.state["calls"].names,
    )

    # Resident state: one step compensated already, another still standing.
    half = directory / "half.jsonl"
    half_journal = journal.Journal(half)
    half_journal.append(
        "half", "saga.started", steps=["reserve-hotel", "charge-card", "book-flight"]
    )
    half_journal.append("half", "step.started", step="reserve-hotel", attempt=1)
    half_journal.append("half", "step.succeeded", step="reserve-hotel", attempt=1)
    half_journal.append("half", "step.started", step="charge-card", attempt=1)
    half_journal.append("half", "step.succeeded", step="charge-card", attempt=1)
    half_journal.append("half", "step.compensated", step="charge-card", attempt=1)
    resumed = demo.build(half, saga_id="half")
    resumed_outcome = resumed.run()
    check(
        "resuming a half-unwound saga does not run forward",
        resumed_outcome.status == ROLLED_BACK,
        resumed_outcome.status,
    )
    check(
        "the remaining step is compensated",
        resumed.state["calls"].names == ["release-hotel"],
        " -> ".join(resumed.state["calls"].names),
    )

    refuses("an empty saga is refused", lambda: Saga("empty", [], directory / "x.jsonl"), SagaError)
    refuses(
        "duplicate step names are refused",
        lambda: Saga(
            "dup", [Step("a", lambda c: None), Step("a", lambda c: None)], directory / "x.jsonl"
        ),
        SagaError,
    )
    refuses(
        "a step name with a separator is refused",
        lambda: Saga("bad", [Step("a:b", lambda c: None)], directory / "x.jsonl"),
        SagaError,
    )
    refuses(
        "a saga id with a separator is refused",
        lambda: Saga("a/b", [Step("a", lambda c: None)], directory / "x.jsonl"),
        SagaError,
    )

    torn = directory / "torn.jsonl"
    torn.write_text('{"seq": 1, "event": "saga.started", "saga": "s"}\n{"seq": 2, "eve')
    check("a torn final line is dropped", len(journal.read(torn)) == 1)

    broken = directory / "broken.jsonl"
    broken.write_text('{"seq": 1, "event": "saga.started", "saga": "s"}\n{"se\n{"seq": 3}\n')
    refuses(
        "a torn line in the middle is refused", lambda: journal.read(broken), journal.JournalError
    )

    refuses(
        "an unknown event is refused",
        lambda: journal.Journal(directory / "unknown.jsonl").append("s", "step.danced"),
        journal.JournalError,
    )


def main() -> int:
    _results.clear()
    with tempfile.TemporaryDirectory(prefix="saga-selftest-") as directory:
        _run(Path(directory))
    failed = [name for ok, name, _ in _results if not ok]
    for ok, name, detail in _results:
        if not ok:
            print(f"FAIL  {name}" + (f"  ({detail})" if detail else ""))
    if failed:
        print(f"selftest: {len(failed)} of {len(_results)} failed")
        return 1
    print(f"selftest: {len(_results)} checks passed")
    return 0
