from __future__ import annotations

from {{ package_name }} import journal
from {{ package_name }}.runner import COMPLETED, ROLLED_BACK, Saga, Step


def _saga(path, calls, *, failing=None):
    def make(name):
        def run(context):
            calls.append(name)
            if failing == name:
                raise RuntimeError(f"{name} failed")
            return None

        def undo(context):
            calls.append(f"undo-{name}")

        return Step(name, run, undo)

    return Saga("trip", [make("a"), make("b"), make("c")], path)


def test_re_running_a_completed_saga_does_nothing(tmp_path):
    path = tmp_path / "j.jsonl"
    calls: list[str] = []
    assert _saga(path, calls).run().status == COMPLETED
    first = list(calls)
    again = _saga(path, calls).run()
    assert again.status == COMPLETED
    assert again.resumed
    assert calls == first


def test_a_finished_rollback_is_not_recompensated(tmp_path):
    path = tmp_path / "j.jsonl"
    calls: list[str] = []
    assert _saga(path, calls, failing="c").run().status == ROLLED_BACK
    first = list(calls)
    assert _saga(path, calls, failing="c").run().status == ROLLED_BACK
    assert calls == first


def test_forward_steps_recorded_as_succeeded_are_skipped(tmp_path):
    path = tmp_path / "j.jsonl"
    log = journal.Journal(path)
    log.append("trip", "saga.started", steps=["a", "b", "c"])
    log.append("trip", "step.started", step="a", attempt=1)
    log.append("trip", "step.succeeded", step="a", attempt=1)
    calls: list[str] = []
    outcome = _saga(path, calls).run()
    assert outcome.status == COMPLETED
    assert calls == ["b", "c"]
    assert outcome.resumed


def test_an_interrupted_step_is_retried_with_the_same_key(tmp_path):
    path = tmp_path / "j.jsonl"
    log = journal.Journal(path)
    log.append("trip", "saga.started", steps=["a", "b", "c"])
    log.append("trip", "step.started", step="a", key="trip:a", attempt=1)
    calls: list[str] = []
    outcome = _saga(path, calls).run()
    assert outcome.status == COMPLETED
    assert calls == ["a", "b", "c"]
    started = [record for record in journal.read(path) if record["event"] == "step.started"]
    keys = [record.get("key") for record in started if record["step"] == "a"]
    assert keys == ["trip:a", "trip:a"]
    assert any(record["event"] == "step.retried" for record in journal.read(path))


def test_a_partly_compensated_saga_resumes_into_rollback_not_forward(tmp_path):
    path = tmp_path / "j.jsonl"
    log = journal.Journal(path)
    log.append("trip", "saga.started", steps=["a", "b", "c"])
    for name in ("a", "b"):
        log.append("trip", "step.started", step=name, attempt=1)
        log.append("trip", "step.succeeded", step=name, attempt=1)
    log.append("trip", "step.started", step="c", attempt=1)
    log.append("trip", "step.failed", step="c", attempt=1, detail="RuntimeError: c failed")
    log.append("trip", "step.compensated", step="b", attempt=1)
    calls: list[str] = []
    outcome = _saga(path, calls).run()
    assert outcome.status == ROLLED_BACK
    assert calls == ["undo-a"]
    assert outcome.statuses["c"] == "failed"
