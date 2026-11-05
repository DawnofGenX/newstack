"""The runner turns every outcome into a written record."""

from __future__ import annotations

from {{ package_name }}.client import RequestFailed
from {{ package_name }}.records import (
    Request,
    ResultWriter,
    load_results,
)
from {{ package_name }}.runner import Summary, run


class Counter:
    """Answers every prompt, failing the ones listed in `fail_on`."""

    model = "counter"

    def __init__(self, fail_on: set[str] | None = None) -> None:
        self.fail_on = fail_on or set()
        self.seen: list[str] = []

    def complete(self, prompt: str) -> tuple[str, int, int, int]:
        self.seen.append(prompt)
        if prompt in self.fail_on:
            raise RequestFailed("http 500")
        return f"answer to {prompt}", 2, 3, 1


def test_every_request_gets_a_line(tmp_path) -> None:
    out = tmp_path / "results.jsonl"
    with ResultWriter(out) as writer:
        summary = run(
            [Request(id=f"r{index}", prompt="p") for index in range(6)],
            Counter(),  # type: ignore[arg-type]
            writer,
            concurrency=3,
        )
    assert (summary.total, summary.ok, summary.failed) == (6, 6, 0)
    assert summary.tokens_in == 12
    assert summary.tokens_out == 18
    assert len(load_results(out)) == 6


def test_a_failure_is_recorded_and_the_run_continues(tmp_path) -> None:
    out = tmp_path / "results.jsonl"
    with ResultWriter(out) as writer:
        summary = run(
            [Request(id="good", prompt="p"), Request(id="bad", prompt="boom")],
            Counter({"boom"}),  # type: ignore[arg-type]
            writer,
            concurrency=2,
        )
    assert summary.ok == 1
    assert summary.failed == 1
    assert summary.failures == ["bad: http 500"]
    done = load_results(out)
    assert done["bad"].ok is False
    assert done["good"].output == "answer to p"


def test_resumed_counts_are_carried_through(tmp_path) -> None:
    pending = [Request(id="a", prompt="p")]
    with ResultWriter(tmp_path / "results.jsonl") as writer:
        summary = run(pending, Counter(), writer, total=5, resumed=4)  # type: ignore[arg-type]
    assert summary.total == 5
    assert summary.resumed == 4
    assert summary.worked == 1


def test_an_empty_batch_does_no_work(tmp_path) -> None:
    with ResultWriter(tmp_path / "results.jsonl") as writer:
        summary = run([], Counter(), writer)  # type: ignore[arg-type]
    assert summary.lines()[1] == "ok        0"


def test_a_bad_concurrency_is_rejected(tmp_path) -> None:
    import pytest

    pending = [Request(id="a", prompt="p")]
    with ResultWriter(tmp_path / "results.jsonl") as writer, pytest.raises(ValueError):
        run(pending, Counter(), writer, concurrency=0)  # type: ignore[arg-type]


def test_summary_lines_are_greppable() -> None:
    lines = Summary(total=4, ok=3, failed=1, resumed=0, tokens_in=9, tokens_out=4).lines()
    assert lines[0] == "requests  4"
    assert "tokens_in 9" in lines
