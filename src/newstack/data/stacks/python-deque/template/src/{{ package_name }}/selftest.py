"""The promises this deque makes, run against the real modules."""

from __future__ import annotations

from dataclasses import dataclass, field

from . import demo
from .solve import (
    MAX_CAPACITY,
    DequeError,
    append,
    append_left,
    audit_deque,
    make_deque,
    peek,
    peek_left,
    pop,
    pop_left,
    rotate,
    to_list,
)


@dataclass
class Report:
    checks: int = 0
    failed: int = 0
    _lines: list = field(default_factory=list)

    def section(self, title: str) -> None:
        self._lines.append(f"## {title}")

    def equal(self, name: str, got, want) -> None:
        self.checks += 1
        if got == want:
            self._lines.append(f"ok   {name}")
        else:
            self.failed += 1
            self._lines.append(f"FAIL {name}: {got!r} != {want!r}")

    def ok(self, name: str, cond: bool) -> None:
        self.checks += 1
        if cond:
            self._lines.append(f"ok   {name}")
        else:
            self.failed += 1
            self._lines.append(f"FAIL {name}")

    def refuses(self, name: str, fn, exc) -> None:
        self.checks += 1
        try:
            fn()
        except exc:
            self._lines.append(f"ok   {name}")
            return
        except Exception as other:
            self.failed += 1
            self._lines.append(f"FAIL {name}: raised {type(other).__name__}")
            return
        self.failed += 1
        self._lines.append(f"FAIL {name}: did not raise")

    def render(self) -> str:
        tail = f"selftest: {self.checks - self.failed} checks passed, {self.failed} failed"
        return "\n".join((*self._lines, "", tail))


FIXTURE = "both ends are first-class, and a rotation never loses an item"


def _door(report: Report) -> None:
    report.section("the door")
    report.equal("empty deque", to_list(make_deque(())), [])
    report.equal("lone value", to_list(make_deque((7,))), [7])
    report.equal("three values", to_list(make_deque((1, 2, 3))), [1, 2, 3])


def _ends(report: Report) -> None:
    report.section("both ends")
    d = make_deque((1, 2, 3))
    report.equal("append right", to_list(append(d, 4)), [1, 2, 3, 4])
    d2 = make_deque((1, 2, 3))
    report.equal("append left", to_list(append_left(d2, 0)), [0, 1, 2, 3])
    report.equal("pop right", pop(make_deque((1, 2, 3))), 3)
    report.equal("pop left", pop_left(make_deque((1, 2, 3))), 1)
    report.equal("peek right", peek(make_deque((1, 2, 3))), 3)
    report.equal("peek left", peek_left(make_deque((1, 2, 3))), 1)
    report.equal("append then pop right", pop(append(make_deque((1, 2)), 3)), 3)
    report.equal("appendleft then popleft", pop_left(append_left(make_deque((1, 2)), 0)), 0)
    report.equal("peek after append", peek(append(make_deque((1, 2)), 3)), 3)
    report.equal("peekleft after appendleft", peek_left(append_left(make_deque((1, 2)), 0)), 0)


def _rotate(report: Report) -> None:
    report.section("rotation")
    report.equal("rotate right 1", to_list(rotate(make_deque((1, 2, 3)), 1)), [3, 1, 2])
    report.equal("rotate left 1", to_list(rotate(make_deque((1, 2, 3)), -1)), [2, 3, 1])
    report.equal("rotate keeps items", sorted(to_list(rotate(make_deque((1, 2, 3)), 2))), [1, 2, 3])
    report.equal("rotate full cycle", to_list(rotate(make_deque((1, 2, 3)), 3)), [1, 2, 3])
    report.equal("rotate zero", to_list(rotate(make_deque((1, 2, 3)), 0)), [1, 2, 3])


def _audit(report: Report) -> None:
    report.section("audit")
    d = make_deque((1, 2, 3))
    report.ok("audit agrees", audit_deque(d, [1, 2, 3]))
    report.ok("audit agrees after append", audit_deque(append(make_deque((1, 2)), 3), [1, 2, 3]))


def _refusal(report: Report) -> None:
    report.section("a bad value is named")
    report.refuses(
        "oversized refused",
        lambda: make_deque(list(range(MAX_CAPACITY + 1))),
        DequeError,
    )
    report.refuses("non-int refused", lambda: make_deque((1, "a")), DequeError)
    report.refuses("pop empty refused", lambda: pop(make_deque(())), DequeError)
    report.refuses("peek empty refused", lambda: peek(make_deque(())), DequeError)


def _stories(report: Report) -> None:
    report.section("the stories the tool tells")
    told = demo.stories()
    report.equal("six stories are told", len(told), 6)
    for story in told:
        report.ok(f"{story.title}: all checks hold", story.held)
    from . import solve as solve_module

    report.ok(
        "the marker the detector looks for is in the deque module",
        FIXTURE in " ".join((solve_module.__doc__ or "").split()).lower(),
    )


def run() -> Report:
    report = Report()
    _door(report)
    _ends(report)
    _rotate(report)
    _audit(report)
    _refusal(report)
    _stories(report)
    return report
