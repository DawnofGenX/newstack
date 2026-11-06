"""The package checking itself, so ``selftest`` needs no test runner."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from . import cli as cli_module
from . import demo as demo_module
from .evaluator import PRECISION, EvalError, as_text, evaluate
from .lexer import LexError, tokenize
from .nodes import Binary
from .parser import ParseError, parse

FIXTURES = Path(__file__).resolve().parent.parent.parent / "fixtures"


class Report:
    def __init__(self) -> None:
        self.checks = 0
        self.failed = 0
        self.lines: list[str] = []

    def section(self, title: str) -> None:
        self.lines.append(f"{title}")

    def _record(self, label: str, problem: str) -> None:
        self.checks += 1
        if problem:
            self.failed += 1
            self.lines.append(f"  FAIL {label}: {problem}")
        else:
            self.lines.append(f"  ok   {label}")

    def ok(self, label: str, holds: bool) -> None:
        self._record(label, "" if holds else "did not hold")

    def equal(self, label: str, actual: object, wanted: object) -> None:
        self._record(label, "" if actual == wanted else f"wanted {wanted!r}, got {actual!r}")

    def refuses(self, label: str, call, needle: str = "") -> None:
        try:
            call()
        except (EvalError, LexError, ParseError) as error:
            self._record(label, "" if needle in str(error) else f"message lacked {needle!r}")
        except Exception as error:  # a wrong exception type is the failure
            self._record(label, f"raised {type(error).__name__}: {error}")
        else:
            self._record(label, "did not raise")

    def render(self) -> str:
        return "\n".join(
            [*self.lines, f"selftest: {self.checks} checks passed, {self.failed} failed"]
        )


def _value(expression: str, *, inexact: bool = True) -> str:
    return as_text(evaluate(parse(expression), exact=not inexact))


def _checks_lexing(report: Report) -> None:
    report.section("lexing")
    tokens = tokenize("12 + x3 <= 4.5e2")
    report.equal("five tokens and an end", len(tokens), 6)
    report.equal("the number keeps its value", tokens[0].value, Decimal("12"))
    report.equal("the name keeps its text", tokens[2].value, "x3")
    report.equal("the comparison is one token", tokens[3].text, "<=")
    report.equal("the exponent is a number", tokens[4].value, Decimal("4.5E+2"))
    report.equal("columns are one-based", tokens[2].column, 6)
    report.refuses("a stray character is refused", lambda: tokenize("2 $ 3"), "not a token")
    report.refuses("a dangling dot is refused", lambda: tokenize("1."), "no digits after")
    report.refuses("a dangling exponent is refused", lambda: tokenize("1e"), "no digits after")


def _checks_precedence(report: Report) -> None:
    report.section("precedence")
    tree = parse("2 + 3 * 4")
    report.ok("the sum is the root", isinstance(tree, Binary) and tree.op == "+")
    report.ok(
        "the product is the right child", isinstance(tree.right, Binary) and tree.right.op == "*"
    )
    report.equal("it evaluates to fourteen", _value("2 + 3 * 4"), "14")
    report.equal("parentheses change it", _value("(2 + 3) * 4"), "20")
    report.equal("minus is left-associative", _value("1 - 2 - 3"), "-4")
    report.equal("division is left-associative", _value("8 / 4 / 2"), "1")
    report.equal("the comparison is the loosest binding", _value("1 + 2 < 4"), "1")
    report.equal("comparison with a product on the right", _value("1 < 2 * 3"), "1")


def _checks_associativity(report: Report) -> None:
    report.section("associativity")
    report.equal("the power gathers to the right", _value("2 ^ 3 ^ 2"), "512")
    report.equal("grouping left gives another number", _value("(2 ^ 3) ^ 2"), "64")
    report.ok("the tree of 2 ^ 3 ^ 2 is right-nested", isinstance(parse("2 ^ 3 ^ 2").right, Binary))
    report.equal("minus binds looser than a power", _value("-2 ^ 2"), "-4")
    report.equal("parentheses give minus two squared", _value("(-2) ^ 2"), "4")
    report.equal("a negative exponent is allowed", _value("2 ^ -1"), "0.5")
    report.equal("double negation is a no-op", _value("--3"), "3")


def _checks_printing(report: Report) -> None:
    report.section("printing")
    corpus = [
        "1 + 2 * 3",
        "(1 + 2) * 3",
        "2 ^ 3 ^ 2",
        "(2 ^ 3) ^ 2",
        "-2 ^ 2",
        "(-2) ^ 2",
        "1 - (2 - 3)",
        "1 - 2 - 3",
        "max(1, 2, 3) / 2",
        "-(1 + 2) * 3",
        "a + b * c",
    ]
    for expression in corpus:
        tree = parse(expression)
        report.ok(f"{expression} round-trips", parse(tree.render()) == tree)
    report.equal("a redundant parenthesis is dropped", parse("(2 * 3) + 4").render(), "2 * 3 + 4")
    report.equal("a needed parenthesis is kept", parse("2 * (3 + 4)").render(), "2 * (3 + 4)")
    report.equal(
        "the right side of a minus keeps its group", parse("1 - (2 - 3)").render(), "1 - (2 - 3)"
    )
    report.equal("a decimal keeps no trailing zeros", _value("1.500 + 0"), "1.5")
    report.equal("minus zero prints as zero", _value("-0"), "0")


def _checks_exactness(report: Report) -> None:
    report.section("exactness")
    report.equal("a tenth plus two tenths", as_text(evaluate(parse("0.1 + 0.2"))), "0.3")
    report.equal("an eighth is finite", as_text(evaluate(parse("1 / 8"))), "0.125")
    report.refuses(
        "a third is refused", lambda: evaluate(parse("1 / 3")), "no finite decimal expansion"
    )
    rounded = as_text(evaluate(parse("1 / 3"), exact=False))
    report.equal("rounding keeps the promised digits", len(rounded.split(".")[1]), PRECISION)
    report.refuses(
        "division by zero is refused", lambda: evaluate(parse("1 / 0"), exact=False), "division"
    )
    report.refuses(
        "a fraction of a power is refused", lambda: evaluate(parse("4 ^ 0.5")), "fractional power"
    )
    report.equal("sqrt of a square is exact", as_text(evaluate(parse("sqrt(81)"))), "9")
    report.refuses(
        "sqrt of a non-square is refused", lambda: evaluate(parse("sqrt(2)")), "does not terminate"
    )
    report.ok(
        "the rounded sqrt is close",
        as_text(evaluate(parse("sqrt(2)"), exact=False)).startswith("1.4142"),
    )
    report.equal("min and max take many arguments", _value("max(1, 7, 3) - min(1, 7, 3)"), "6")
    report.equal("round halves away from zero", _value("round(2.5)"), "3")


def _checks_errors(report: Report) -> None:
    report.section("errors")
    report.refuses("an operator with no left operand", lambda: parse("2 + * 3"), "column 5")
    report.refuses("an unclosed group", lambda: parse("1 + (2"), "opened at column 5")
    report.refuses("a chained comparison", lambda: parse("1 < 2 < 3"), "chain")
    report.refuses("a name with no value", lambda: evaluate(parse("x + 1")), "not defined")
    report.refuses(
        "a function that does not exist", lambda: evaluate(parse("nope(1)")), "not a function"
    )
    report.refuses("a call with no arguments", lambda: parse("abs()"), "no arguments")
    report.refuses("trailing text", lambda: parse("1 + 2 3"), "after a complete expression")
    report.refuses("an empty expression", lambda: parse(""), "expected a number")
    report.equal("the caret sits under the column", _caret_of("2 + * 3").index("^"), 6)


def _caret_of(expression: str) -> str:
    try:
        parse(expression)
    except ParseError as error:
        return error.caret().splitlines()[-1]
    raise AssertionError("expected a refusal")


def _checks_fixtures(report: Report) -> None:
    report.section("fixtures")
    path = FIXTURES / "expressions.txt"
    report.ok("the fixture exists", path.is_file())
    rows = [line.strip() for line in path.read_text().splitlines() if line.strip()]
    report.ok("the fixture has rows", len(rows) >= 10)
    good = 0
    for row in rows:
        source, _, expected = row.partition("=")
        source, expected = source.strip(), expected.strip()
        if not expected:
            continue
        try:
            value = as_text(evaluate(parse(source), exact=False))
        except (EvalError, ParseError, LexError):
            report.ok(f"{source} evaluates", False)
            continue
        good += 1
        report.ok(f"{source} = {expected}", value == expected)
    report.ok("most rows were checked", good >= 10)


def _checks_stories(report: Report) -> None:
    report.section("stories")
    text = demo_module.render_stories()
    report.ok("every story holds", text.endswith("6 of 6 hold"))
    report.ok("the footer is printed once", text.count("stories      ") == 1)


def _checks_command_line(report: Report) -> None:
    report.section("command line")
    built = cli_module.build_parser().parse_args(["eval", "1"])
    report.ok("eval routes to its handler", built.handler is cli_module._command_eval)
    report.ok(
        "the program name is set",
        cli_module.PROGRAM == "{{ npm_name }}",
    )
    report.ok(
        "the exit codes are distinct",
        len({cli_module.EXIT_OK, cli_module.EXIT_REFUSED, cli_module.EXIT_UNUSABLE}) == 3,
    )
    report.equal("the version is a version", cli_module.VERSION.count("."), 2)
    report.ok("a bad --var is a usage error", _usage_refused("--var", "x"))


def _usage_refused(flag: str, value: str) -> bool:
    try:
        cli_module._values([value])
    except cli_module.UsageError:
        return True
    return False


def run() -> Report:
    report = Report()
    _checks_lexing(report)
    _checks_precedence(report)
    _checks_associativity(report)
    _checks_printing(report)
    _checks_exactness(report)
    _checks_errors(report)
    _checks_fixtures(report)
    _checks_stories(report)
    _checks_command_line(report)
    return report
