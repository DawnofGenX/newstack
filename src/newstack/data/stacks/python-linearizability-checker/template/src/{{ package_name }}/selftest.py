"""Known answers, checked without pytest, so the CI can run the same claims anywhere."""

from __future__ import annotations

from pathlib import Path

from . import cli as cli_module
from .check import brute_force, check, is_minimal, shrink
from .demo import run_stories
from .explain import account_lines, verdict_lines
from .history import READ, WRITE, History, HistoryError, Operation, parse_lines

FIXTURES = Path(__file__).resolve().parent.parent.parent / "fixtures"


def _op(client: int, kind: str, value: int, start: int, end: int) -> Operation:
    return Operation(client=client, kind=kind, value=value, start=start, end=end)


class Report:
    def __init__(self) -> None:
        self.checks = 0
        self.failed = 0
        self.lines: list[str] = []

    def section(self, title: str) -> None:
        self.lines.append(title)

    def ok(self, claim: str, holds: bool) -> None:
        self.checks += 1
        if holds:
            self.lines.append(f"  ok   {claim}")
            return
        self.failed += 1
        self.lines.append(f"  FAIL {claim}")

    def equal(self, claim: str, found: object, expected: object) -> None:
        self.ok(f"{claim} ({found!r})", found == expected)

    def check(self, claim: str, verdict) -> None:
        self.ok(f"{claim}: {verdict.verdict}", verdict.linearizable)

    def refuses(self, claim: str, action, error: type[BaseException]) -> None:
        try:
            action()
        except error as raised:
            self.ok(f"{claim} ({raised})", True)
            return
        except Exception as raised:
            self.ok(f"{claim} raised {type(raised).__name__}: {raised}", False)
            return
        self.ok(f"{claim} was accepted", False)

    def render(self) -> str:
        tail = f"selftest: {self.checks} checks passed, {self.failed} failed"
        self.lines.append(tail)
        return "\n".join(self.lines)

    def finish(self) -> int:
        print(self.render())
        return 0 if self.failed == 0 else 1


def _reading(report: Report) -> None:
    report.section("reading")
    history = parse_lines(
        [
            '{"initial": 4}',
            '{"client": 0, "op": "write", "value": 5, "start": 0, "end": 1}',
            "",
            "# a comment",
            '{"client": 0, "op": "read", "value": 5, "start": 2, "end": 3}',
        ]
    )
    report.equal("two operations are read", len(history), 2)
    report.equal("the header sets the initial value", history.initial, 4)
    report.equal("the source of a memory history is named", history.source, "<memory>")
    report.refuses(
        "an overlapping programme is refused",
        lambda: parse_lines(
            [
                '{"client": 0, "op": "write", "value": 1, "start": 0, "end": 5}',
                '{"client": 0, "op": "read", "value": 1, "start": 4, "end": 6}',
            ]
        ),
        HistoryError,
    )
    report.refuses(
        "a response before its invocation is refused",
        lambda: parse_lines(['{"client": 0, "op": "read", "value": 1, "start": 5, "end": 1}']),
        HistoryError,
    )
    report.refuses(
        "an unknown key is refused",
        lambda: parse_lines(
            ['{"client": 0, "op": "read", "value": 1, "start": 1, "end": 2, "note": "typo"}']
        ),
        HistoryError,
    )
    report.refuses(
        "a missing key is refused",
        lambda: parse_lines(['{"client": 0, "op": "read", "value": 1, "start": 1}']),
        HistoryError,
    )
    report.refuses(
        "an unknown kind is refused",
        lambda: parse_lines(['{"client": 0, "op": "scan", "value": 1, "start": 1, "end": 2}']),
        HistoryError,
    )
    report.refuses(
        "a boolean time is refused",
        lambda: parse_lines(['{"client": 0, "op": "read", "value": 1, "start": true, "end": 2}']),
        HistoryError,
    )


def _search(report: Report) -> None:
    report.section("search")
    sequential = History(
        (_op(0, WRITE, 5, 0, 2), _op(0, READ, 5, 3, 4), _op(0, WRITE, 7, 5, 6)), initial=0
    )
    verdict = check(sequential)
    report.check("a sequential history is accepted", verdict)
    report.equal("and its witness is the programme order", verdict.order, (0, 1, 2))

    empty = History(())
    report.check("the empty history is accepted", check(empty))
    report.equal("an empty search visits no node", check(empty).nodes, 0)

    stale = History((_op(0, WRITE, 5, 0, 2), _op(1, READ, 3, 3, 4)), initial=0)
    report.ok("an invented value is refused", not check(stale).linearizable)

    straddle = History(
        (_op(0, WRITE, 1, 0, 10), _op(1, READ, 0, 1, 2), _op(1, READ, 1, 3, 4)), initial=0
    )
    verdict = check(straddle)
    report.check("a write may land between two reads", verdict)
    report.equal("the witness puts it there", verdict.order, (1, 0, 2))

    late = History((_op(0, WRITE, 5, 0, 2), _op(1, READ, 0, 3, 4)), initial=0)
    report.ok("a read after the response cannot miss the write", not check(late).linearizable)

    overlapping = History((_op(0, WRITE, 5, 0, 2), _op(1, READ, 0, 1, 4)), initial=0)
    report.ok("the same read overlapping may miss it", check(overlapping).linearizable)

    two_writers = History(
        (_op(0, WRITE, 1, 0, 3), _op(1, WRITE, 2, 1, 4), _op(2, READ, 2, 5, 6)), initial=0
    )
    report.check("concurrent writers can be ordered either way", check(two_writers))

    report.equal(
        "the initial value is the value before any write",
        check(History((_op(0, READ, 9, 0, 1),))).linearizable,
        False,
    )
    report.check(
        "and a fresh register reads its initial value", check(History((_op(0, READ, 0, 0, 1),)))
    )


def _shrinking(report: Report) -> None:
    report.section("shrinking")
    history = History(
        (
            _op(0, WRITE, 1, 0, 1),
            _op(1, READ, 0, 2, 3),
            _op(2, WRITE, 9, 4, 5),
            _op(1, READ, 9, 6, 7),
        ),
        initial=0,
    )
    report.ok("the history is refused", not check(history).linearizable)
    core, verdict = shrink(history)
    report.ok("the core is smaller than the history", len(core) < len(history))
    invented = History((_op(0, WRITE, 5, 0, 2), _op(1, READ, 3, 3, 4)), initial=0)
    report.equal("an invented value needs no second operation", len(shrink(invented)[0]), 1)
    report.ok("the core is still refused", not verdict.linearizable)
    report.ok("removing any one operation clears the core", is_minimal(core))
    report.equal(
        "shrinking a good history is a no-op", len(shrink(History((_op(0, READ, 0, 0, 1),)))[0]), 1
    )


def _yardstick(report: Report) -> None:
    report.section("yardstick")
    history = History(
        (
            _op(0, WRITE, 1, 0, 1),
            _op(1, READ, 1, 2, 3),
            _op(2, WRITE, 2, 2, 4),
            _op(3, READ, 2, 5, 6),
            _op(4, WRITE, 3, 5, 7),
            _op(5, READ, 3, 8, 9),
            _op(6, READ, 0, 0, 0),
        ),
        initial=0,
    )
    fast = check(history)
    slow = brute_force(history)
    report.equal("the two checkers agree", fast.linearizable, slow.linearizable)
    report.equal("on the same witness", fast.order, slow.order)
    report.ok("the yardstick tries whole orders", slow.nodes > 100)
    report.ok("the search visits far fewer nodes", fast.nodes * 10 < slow.nodes)
    report.refuses(
        "brute force refuses a history that is too big",
        lambda: brute_force(History(tuple(_op(0, READ, 0, i, i + 1) for i in range(9)))),
        ValueError,
    )


def _fixtures(report: Report) -> None:
    report.section("fixtures")
    from .history import load

    sequential = load(FIXTURES / "sequential.jsonl")
    report.equal("the sequential fixture has three operations", len(sequential), 3)
    report.check("and is accepted", check(sequential))

    stale = load(FIXTURES / "stale-read.jsonl")
    report.ok("the stale-read fixture is refused", not check(stale).linearizable)

    straddle = load(FIXTURES / "straddle.jsonl")
    report.check("the straddle fixture is accepted", check(straddle))

    report.refuses(
        "a missing file is refused",
        lambda: load(FIXTURES / "nope.jsonl"),
        HistoryError,
    )


def _command_line(report: Report) -> None:
    report.section("command line")
    parser = cli_module.build_parser()
    report.ok(
        "selftest routes to its own handler",
        parser.parse_args(["selftest"]).handler is cli_module._command_selftest,
    )
    report.equal(
        "the program name is set",
        cli_module.PROGRAM,
        "{{ npm_name }}",
    )
    report.equal(
        "the exit codes are distinct",
        len({cli_module.EXIT_OK, cli_module.EXIT_REFUSED, cli_module.EXIT_UNUSABLE}),
        3,
    )
    story_report = run_stories()
    report.equal("every demo story holds", sum(1 for story in story_report if story.held), 6)


def _rendering(report: Report) -> None:
    report.section("rendering")
    history = History((_op(0, WRITE, 1, 0, 1), _op(1, READ, 1, 2, 3)), initial=0)
    lines = verdict_lines(history, check(history))
    report.ok("a witness is printed", any(line.startswith("witness") for line in lines))
    report.ok("the search is counted", any(line.startswith("search") for line in lines))
    account = account_lines(history)
    report.equal("the account covers both clients", len(account), 4)
    bad = History((_op(0, WRITE, 5, 0, 2), _op(1, READ, 0, 3, 4)), initial=0)
    refused = verdict_lines(bad, check(bad))
    report.ok("a refusal names the core", any(line.startswith("core") for line in refused))


def run() -> int:
    report = Report()
    _reading(report)
    _search(report)
    _shrinking(report)
    _yardstick(report)
    _fixtures(report)
    _command_line(report)
    _rendering(report)
    return report.finish()
