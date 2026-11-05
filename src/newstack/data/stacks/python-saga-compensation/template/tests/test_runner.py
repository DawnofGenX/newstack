from __future__ import annotations

import pytest

from {{ package_name }} import journal
from {{ package_name }} import runner as subject
from {{ package_name }}.runner import Saga, SagaError, Step

COMPLETED = subject.COMPLETED
INCOMPLETE = subject.INCOMPLETE
ROLLED_BACK = subject.ROLLED_BACK


def test_a_clean_run_completes(tmp_path):
    calls: list[str] = []
    saga = Saga(
        "clean",
        [
            Step("a", lambda context: calls.append("a")),
            Step("b", lambda context: calls.append("b")),
        ],
        tmp_path / "j.jsonl",
    )
    outcome = saga.run()
    assert outcome.status == COMPLETED
    assert calls == ["a", "b"]
    assert outcome.statuses == {"a": "succeeded", "b": "succeeded"}
    assert not outcome.resumed


def test_failure_compensates_in_reverse_order(tmp_path):
    calls: list[str] = []

    def fail(context):
        raise RuntimeError("nope")

    saga = Saga(
        "reverse",
        [
            Step("a", lambda c: calls.append("a"), lambda c: calls.append("undo-a")),
            Step("b", lambda c: calls.append("b"), lambda c: calls.append("undo-b")),
            Step("c", fail, lambda c: calls.append("undo-c")),
        ],
        tmp_path / "j.jsonl",
    )
    outcome = saga.run()
    assert outcome.status == ROLLED_BACK
    assert outcome.failed_step == "c"
    assert calls == ["a", "b", "undo-b", "undo-a"]


def test_the_failing_step_is_not_compensated(tmp_path):
    nos = []

    def fail(context):
        raise RuntimeError("nope")

    saga = Saga(
        "failing",
        [
            Step("a", lambda c: None, lambda c: nos.append("a")),
            Step("b", fail, lambda c: nos.append("b")),
        ],
        tmp_path / "j.jsonl",
    )
    saga.run()
    assert nos == ["a"]


def test_a_missing_compensation_makes_the_rollback_incomplete(tmp_path):
    def fail(context):
        raise RuntimeError("nope")

    saga = Saga(
        "irreversible",
        [Step("email", lambda c: None), Step("charge", fail)],
        tmp_path / "j.jsonl",
    )
    outcome = saga.run()
    assert outcome.status == INCOMPLETE
    assert "email: no compensation was declared" in outcome.unrecoverable
    assert outcome.statuses["email"] == "unrecoverable"


def test_one_broken_compensation_does_not_stop_the_others(tmp_path):
    calls: list[str] = []

    def fail(context):
        raise RuntimeError("nope")

    def broken(context):
        raise RuntimeError("the refund endpoint is down")

    saga = Saga(
        "stuck",
        [
            Step("hotel", lambda c: None, lambda c: calls.append("release")),
            Step("card", lambda c: None, broken),
            Step("flight", fail),
        ],
        tmp_path / "j.jsonl",
    )
    outcome = saga.run()
    assert outcome.status == INCOMPLETE
    assert outcome.statuses["card"] == "compensation_failed"
    assert calls == ["release"]
    assert "card: every compensation attempt failed" in outcome.unrecoverable


def test_a_transient_failure_is_retried(tmp_path):
    attempts: list[int] = []

    def flaky(context):
        attempts.append(context.attempt)
        if context.attempt == 1:
            raise TimeoutError("slow")

    saga = Saga(
        "retry", [Step("a", flaky, max_attempts=2, retry_on=(TimeoutError,))], tmp_path / "j.jsonl"
    )
    assert saga.run().status == COMPLETED
    assert attempts == [1, 2]


def test_retry_on_refuses_to_retry_something_else(tmp_path):
    attempts: list[int] = []

    def wrong(context):
        attempts.append(context.attempt)
        raise ValueError("not transient")

    saga = Saga(
        "filter", [Step("a", wrong, max_attempts=3, retry_on=(TimeoutError,))], tmp_path / "j.jsonl"
    )
    assert saga.run().status == ROLLED_BACK
    assert attempts == [1]


def test_retries_share_one_idempotency_key(tmp_path):
    path = tmp_path / "j.jsonl"

    def flaky(context):
        if context.attempt == 1:
            raise TimeoutError("slow")

    Saga("keyed", [Step("a", flaky, max_attempts=2)], path).run()
    keys = [record["key"] for record in journal.read(path) if record["event"] == "step.started"]
    assert len(keys) == 2
    assert len(set(keys)) == 1


def test_a_saga_needs_steps(tmp_path):
    with pytest.raises(SagaError, match="no steps"):
        Saga("empty", [], tmp_path / "j.jsonl")


def test_duplicate_step_names_are_refused(tmp_path):
    with pytest.raises(SagaError, match="duplicate"):
        Saga("dup", [Step("a", lambda c: None), Step("a", lambda c: None)], tmp_path / "j.jsonl")


@pytest.mark.parametrize("name", ["", "a:b", "a/b"])
def test_step_names_cannot_carry_separators(tmp_path, name):
    with pytest.raises(SagaError):
        Step(name, lambda c: None)


def test_a_step_needs_an_attempt(tmp_path):
    with pytest.raises(SagaError, match="max_attempts"):
        Step("a", lambda c: None, max_attempts=0)


def test_the_outcome_renders_greppable_lines(tmp_path):
    saga = Saga("lines", [Step("a", lambda c: None)], tmp_path / "j.jsonl")
    rendered = "\n".join(saga.run().lines())
    assert "status     completed" in rendered
    assert "step       a                    succeeded" in rendered
