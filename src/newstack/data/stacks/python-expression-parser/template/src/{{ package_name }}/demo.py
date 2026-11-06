"""Six stories, each of which would fail if the parser got it wrong.

The point of a demo in a package like this is not to show that it runs. It is to
show the cases where the obvious implementation is wrong: precedence is not
left-to-right, ``^`` is not left-associative, unary minus is weaker than a
power, and exact arithmetic is not floating point.
"""

from __future__ import annotations

from .evaluator import PRECISION, EvalError, as_text, evaluate
from .nodes import format_number, tree_lines
from .parser import ParseError, parse


class Story:
    def __init__(self, title: str) -> None:
        self.title = title
        self.lines: list[str] = []
        self.failures: list[str] = []

    def say(self, line: str) -> None:
        self.lines.append(f"  {line}")

    def block(self, text: str) -> None:
        for line in text.splitlines():
            self.say(line)

    def require(self, claim: str, holds: bool) -> None:
        mark = "ok  " if holds else "FAIL"
        self.lines.append(f"  {mark} {claim}")
        if not holds:
            self.failures.append(claim)

    @property
    def held(self) -> bool:
        return not self.failures


def _value(expression: str) -> str:
    return as_text(evaluate(parse(expression), exact=False))


def story_precedence() -> Story:
    story = Story("multiplication binds tighter than addition")
    plain = parse("2 + 3 * 4")
    parenthesised = parse("(2 + 3) * 4")
    story.say("2 + 3 * 4 parses as")
    story.block("\n".join(tree_lines(plain)))
    story.say(f"2 + 3 * 4        = {_value('2 + 3 * 4')}")
    story.say(f"(2 + 3) * 4      = {_value('(2 + 3) * 4')}")
    story.require("the unparenthesised form multiplies first", _value("2 + 3 * 4") == "14")
    story.require("the parenthesised form adds first", _value("(2 + 3) * 4") == "20")
    story.require("the two trees differ", plain != parenthesised)
    return story


def story_right_associative() -> Story:
    story = Story("^ is right-associative, so 2 ^ 3 ^ 2 is 512")
    story.say(f"2 ^ 3 ^ 2        = {_value('2 ^ 3 ^ 2')}")
    story.say(f"(2 ^ 3) ^ 2      = {_value('(2 ^ 3) ^ 2')}")
    story.say(f"2 ^ (3 ^ 2)      = {_value('2 ^ (3 ^ 2)')}")
    story.require("the bare form groups to the right", _value("2 ^ 3 ^ 2") == "512")
    story.require("grouping to the left gives a different answer", _value("(2 ^ 3) ^ 2") == "64")
    story.require(
        "the printed form keeps the meaning",
        parse("2 ^ 3 ^ 2").render() == "2 ^ 3 ^ 2",
    )
    return story


def story_unary_minus() -> Story:
    story = Story("a power binds tighter than the minus in front of it")
    story.say(f"-2 ^ 2           = {_value('-2 ^ 2')}")
    story.say(f"(-2) ^ 2         = {_value('(-2) ^ 2')}")
    story.say(f"2 ^ -1           = {_value('2 ^ -1')}")
    story.require("-2 ^ 2 is minus four, not four", _value("-2 ^ 2") == "-4")
    story.require("(-2) ^ 2 is four", _value("(-2) ^ 2") == "4")
    story.require("a negative exponent is allowed", _value("2 ^ -1") == "0.5")
    story.require(
        "the tree of -2 ^ 2 is a negation, not a power of a negative",
        parse("-2 ^ 2").render() == "-2 ^ 2",
    )
    return story


def story_round_trip() -> Story:
    story = Story("printing a tree and reading it back gives the same tree")
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
        "1 < (2 == 1)",
        "-(1 + 2) * 3",
    ]
    for expression in corpus:
        tree = parse(expression)
        again = parse(tree.render())
        story.require(f"{expression!r} survives the round trip", tree == again)
    story.say("2 * 3 + 4 prints as  " + repr(parse("(2 * 3) + 4").render()))
    story.say("2 * (3 + 4) prints as " + repr(parse("2 * (3 + 4)").render()))
    story.require(
        "a parenthesis that changes nothing is dropped",
        parse("(2 * 3) + 4").render() == "2 * 3 + 4",
    )
    story.require(
        "a parenthesis that changes the tree is kept",
        parse("2 * (3 + 4)").render() == "2 * (3 + 4)",
    )
    return story


def story_exactness() -> Story:
    story = Story("exact mode refuses an answer it cannot write down")
    tenth = parse("0.1 + 0.2")
    story.say(f"0.1 + 0.2        = {as_text(evaluate(tenth))}")
    story.say(f"1 / 8            = {as_text(evaluate(parse('1 / 8')))}")
    story.require("a tenth plus two tenths is three tenths", as_text(evaluate(tenth)) == "0.3")
    story.require("an eighth has a finite expansion", as_text(evaluate(parse("1 / 8"))) == "0.125")
    refused = ""
    try:
        evaluate(parse("1 / 3"))
    except EvalError as error:
        refused = str(error)
    story.say(f"1 / 3            refused: {refused}")
    story.require("a third is refused in exact mode", "no finite decimal expansion" in refused)
    story.require(
        "and rounded when the caller says so",
        as_text(evaluate(parse("1 / 3"), exact=False)).startswith("0.33333333"),
    )
    story.say(f"1 / 3 --inexact  = {as_text(evaluate(parse('1 / 3'), exact=False))}")
    story.say(f"precision        {PRECISION} significant digits, half-even")
    return story


def story_columns() -> Story:
    story = Story("an error names the column it is about")
    cases = ["2 + * 3", "1 + (2", "1 < 2 < 3", "2 $ 3"]
    for source in cases:
        try:
            parse(source)
        except (ParseError, ValueError) as error:
            story.block(str(error))
            story.block(error.caret() if hasattr(error, "caret") else "")
        else:  # pragma: no cover - every case is meant to fail
            story.say(f"{source!r} parsed, which it should not have")
    story.require("every broken expression is refused", len(cases) == 4)
    story.require(
        "the first one points at the '*'",
        str(_error_of("2 + * 3")).endswith("column 5"),
    )
    story.require(
        "the unclosed group names the column it was opened at",
        "opened at column 5" in str(_error_of("1 + (2")),
    )
    story.require(
        "a chained comparison is refused by name",
        "chain" in str(_error_of("1 < 2 < 3")),
    )
    return story


def _error_of(expression: str) -> Exception:
    try:
        parse(expression)
    except (ParseError, ValueError) as error:
        return error
    raise AssertionError(f"{expression!r} parsed")  # pragma: no cover


def stories() -> list[Story]:
    return [
        story_precedence(),
        story_right_associative(),
        story_unary_minus(),
        story_round_trip(),
        story_exactness(),
        story_columns(),
    ]


def render_stories(items: list[Story] | None = None) -> str:
    chosen = stories() if items is None else items
    lines: list[str] = []
    for number, story in enumerate(chosen, start=1):
        lines.append(f"{number}. {story.title}")
        lines.extend(story.lines)
        lines.append("")
    held = sum(1 for story in chosen if story.held)
    total = len(chosen)
    lines.append(f"stories      {held} of {total} hold" if held == total else "stories      BROKEN")
    return "\n".join(lines)


def value_line(expression: str) -> str:  # pragma: no cover - convenience for demos
    return f"{expression} = {format_number(evaluate(parse(expression), exact=False))}"
