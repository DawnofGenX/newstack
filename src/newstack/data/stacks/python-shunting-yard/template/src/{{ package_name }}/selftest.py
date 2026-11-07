"""The invariants this yard promises, run against the real modules.

Every claim here is the reason the answers can be trusted:
value_of(expr) must equal the shipped recursive-descent oracle on
shipped and seeded corpora; evaluate of to_postfix must equal
value_of directly; the documented precedence and left binding
must answer the way the texts say; unbalanced parentheses and a
division by zero must raise, naming what broke. Runnable in a
fresh checkout: `python -m the-package selftest`.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from tempfile import TemporaryDirectory

from . import demo
from .calc import (
    evaluate,
    value_of,
)
from .corpus import (
    DEFAULT_SEED,
    CorpusError,
    Record,
    Snapshot,
    audit,
    load_records,
    report_lines,
    synthetic,
    write_records,
)
from .expr import (
    MAX_EXPR,
    OPEN,
    ExprError,
    Number,
    Op,
    read_expr,
)
from .oracle import (
    descent,
)
from .yard import (
    balanced,
    postfix_text,
    to_postfix,
)

FIXTURE = "the operator stack yields only to tighter binding"
EXPRS = (
    "7",
    "1 + 2",
    "2 + 3 * 4",
    "8 - 3 - 2",
    "20 / 4 / 2",
    "( 1 + 2 ) * 3",
    "3 + 4 * 2 / ( 1 - 5 ) * 2",
    "7 / 2",
    "0 + 12",
    "2 * ( 3 + 4 ) - 5",
)
TANGLES = (
    "( ( 1 + 2 ) * ( 3 + 4 ) ) / 7",
    "100 - ( 20 - 5 )",
    "9 / 2 / 2",
    "1 + 2 * 3 - 4 / 2",
)


@dataclass
class Report:
    checks: int = 0
    failed: int = 0
    lines: list = field(default_factory=list)

    def section(self, name: str) -> None:
        self.lines.append(f"- {name}")

    def ok(self, claim: str, held: bool) -> None:
        self.checks += 1
        if held:
            self.lines.append(f"  ok   {claim}")
        else:
            self.failed += 1
            self.lines.append(f"  FAIL {claim}")

    def equal(self, claim: str, found: object, expected: object) -> None:
        self.ok(
            f"{claim} ({found!r})"
            if found == expected
            else f"{claim}: {found!r} != {expected!r}",
            found == expected,
        )

    def refuses(self, claim: str, call: object, error: type) -> None:
        try:
            call()  # type: ignore[operator]
        except error as seen:
            self.ok(f"{claim} ({seen})", True)
        except Exception as seen:
            self.ok(f"{claim}: raised {type(seen).__name__}, not {error.__name__}", False)
        else:
            self.ok(f"{claim}: nothing raised", False)

    def render(self) -> str:
        tail = f"selftest: {self.checks - self.failed} checks passed, {self.failed} failed"
        return "\n".join((*self.lines, "", tail))


def _gate(report: Report) -> None:
    report.section("the gate eats expressions and refuses noise")
    report.equal("one number reads as one number", read_expr("7"), [Number(7)])
    report.equal("a space is free", read_expr(" 1 + 2 "), read_expr("1+2"))
    report.refuses("a letter is no expression", lambda: read_expr("a + 1"), ExprError)
    report.refuses("a float is no expression", lambda: read_expr("1.5 + 1"), ExprError)
    report.refuses("a power is no expression", lambda: value_of("2 ** 3"), ExprError)
    report.refuses("a leading zero is no number", lambda: read_expr("07 + 1"), ExprError)
    report.refuses("the empty expression answers nothing", lambda: read_expr(""), ExprError)
    report.refuses("a non-string is no expression", lambda: read_expr(7), ExprError)
    report.refuses(
        "one past the ceiling is no expression",
        lambda: read_expr("1" * (MAX_EXPR + 1)),
        ExprError,
    )
    report.equal("the ceiling binds left to right", Op("+").left_associative, True)
    report.equal("* parks tighter than +", Op("*").precedence > Op("+").precedence, True)


def _yard(report: Report) -> None:
    report.section("the yard yields a queue, the queue reckons")
    for expr in EXPRS:
        queue = to_postfix(expr)
        if evaluate(queue) != value_of(expr):
            report.equal(f"{expr!r} reckoned elsewhere", "break", "none")
            return
    report.ok("evaluate(to_postfix(expr)) is value_of(expr), every shipped expr", True)
    report.equal("the queue is postfix text", postfix_text(to_postfix("1 + 2")), "1 2 +")
    report.refuses(
        "a parenthesis sits nowhere in a queue",
        lambda: evaluate([Number(1), OPEN, Number(2)]),
        ExprError,
    )
    report.ok("the yard's queues are balanced", all(balanced(to_postfix(e)) for e in EXPRS))
    report.ok("an infix list is no queue to reckon", not balanced(["1", OPEN]))


def _oracle(report: Report) -> None:
    report.section("the yard and the oracle answer alike")
    for expr in EXPRS:
        if descent(expr) != value_of(expr):
            report.equal(f"{expr!r} parted the pair", "break", "none")
            return
    report.ok("the oracle answers value_of on every shipped expression", True)
    for expr in TANGLES:
        if descent(expr) != value_of(expr):
            report.equal(f"{expr!r} parted the pair", "break", "none")
            return
    report.ok("the oracle answers value_of on every tangle", True)
    report.equal("the oracle eats a token list too", descent(read_expr("6 / 4")), 1)


def _precedence(report: Report) -> None:
    report.section("the documented precedence and binding")
    report.equal("* binds tighter: 2 + 3 * 4 is fourteen", value_of("2 + 3 * 4"), 14)
    report.equal("parentheses rebind: (2 + 3) * 4 is twenty", value_of("( 2 + 3 ) * 4"), 20)
    report.equal("- binds left: 100 - 20 - 5 is seventy-five", value_of("100 - 20 - 5"), 75)
    report.equal("/ binds left: 100 / 5 / 2 is ten", value_of("100 / 5 / 2"), 10)
    report.equal("a division floors: 6 / 4 is one", value_of("6 / 4"), 1)
    report.equal("zero is legal: 0 * 9 is zero", value_of("0 * 9"), 0)


def _edges(report: Report) -> None:
    report.section("unbalanced parens and empty divisors raise")
    report.refuses("an unclosed ( is refused", lambda: value_of("( 1 + 2"), ExprError)
    report.refuses("an extra ) is refused", lambda: value_of("1 + 2 )"), ExprError)
    report.refuses("a ) with nothing open is refused", lambda: to_postfix(") 1 ("), ExprError)
    report.refuses("a divided zero is refused", lambda: value_of("5 / 0"), ExprError)
    report.refuses("a half-eaten sum is refused", lambda: value_of("1 +"), ExprError)
    report.refuses("two numbers in a row are refused", lambda: value_of("1 2"), ExprError)
    report.refuses("a leading operator is refused", lambda: value_of("* 3"), ExprError)
    report.refuses("the oracle refuses the same edges", lambda: descent("5 / 0"), ExprError)


def _corpora(report: Report) -> None:
    report.section("the ledger in, the audit out")
    corpus = synthetic(30, seed=11)
    report.equal("the generator is deterministic", corpus, synthetic(30, seed=11))
    report.ok("the records are distinct", len({r.expr for r in corpus}) == 30)
    report.refuses("no records from zero", lambda: synthetic(0), CorpusError)
    for record in corpus:
        if audit(record):
            report.equal(f"{record.expr!r} audited loud", "break", "none")
            return
    report.ok("the seeded ledger audits silent, record after record", True)
    frozen = Snapshot(tuple(r.expr for r in corpus), DEFAULT_SEED)
    thawed = Snapshot.loads(frozen.dumps())
    report.equal("a snapshot replays its expressions", list(thawed.exprs), [r.expr for r in corpus])
    report.refuses(
        "half a snapshot is no snapshot", lambda: Snapshot.loads('{"seed": 1}'),
        CorpusError,
    )
    with TemporaryDirectory() as room:
        path = f"{room}/records.txt"
        write_records(corpus, path)
        report.equal("a written ledger reads back", load_records(path), corpus)
        report.refuses(
            "a missing ledger is named", lambda: load_records(f"{room}/missing.txt"),
            CorpusError,
        )
        noise = f"{room}/noise.txt"
        with open(noise, "w", encoding="utf-8") as handle:
            handle.write("1 + 2 | junk\n")
        report.refuses("a noisy ledger is refused", lambda: load_records(noise), CorpusError)
    report.ok("the report answers every record", len(report_lines(corpus)) == len(corpus))
    report.ok(
        "a forged record is named",
        bool(audit(Record("1 + 2", "1 2 +", 99))),
    )
    report.ok(
        "a forged queue is named",
        bool(audit(Record("1 + 2", "1 + 2", 3))),
    )


def _tangles(report: Report) -> None:
    report.section("the tangle: a random walk, answered twice")
    for seed in (5, 31):
        rng = random.Random(seed)
        broke = False
        for _step in range(80):
            terms = [str(rng.randint(0, 40))]
            for _pair in range(rng.randint(1, 5)):
                terms.append(rng.choice("+-*/"))
                terms.append(str(rng.randint(1, 15)))
            expr = " ".join(terms)
            try:
                if value_of(expr) != descent(expr):
                    broke = True
                    break
                if evaluate(to_postfix(expr)) != value_of(expr):
                    broke = True
                    break
            except ExprError:
                broke = True
                break
        report.ok(f"eighty tangles answered alike (seed {seed})", not broke)


def _stories(report: Report) -> None:
    report.section("the stories the tool tells")
    told = demo.stories()
    report.equal("six stories are told", len(told), 6)
    for story in told:
        report.ok(f"{story.title}: all checks hold", story.held)
    from . import yard as yard_module

    report.ok(
        "the marker the detector looks for is in the yard module",
        FIXTURE in " ".join((yard_module.__doc__ or "").split()).lower(),
    )


def run() -> Report:
    report = Report()
    _gate(report)
    _yard(report)
    _oracle(report)
    _precedence(report)
    _edges(report)
    _corpora(report)
    _tangles(report)
    _stories(report)
    return report
