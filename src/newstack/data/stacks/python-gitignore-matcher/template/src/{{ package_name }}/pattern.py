"""A pattern is a rule: what it matches, where it is anchored, and in which order."""

from __future__ import annotations

import re
from dataclasses import dataclass


class PatternError(ValueError):
    """A pattern that cannot be read as a rule."""


def _unescape_trailing_spaces(text: str) -> str:
    """Trailing spaces are dropped unless a backslash protects them."""
    while text.endswith(" "):
        backslashes = 0
        index = len(text) - 2
        while index >= 0 and text[index] == "\\":
            backslashes += 1
            index -= 1
        if backslashes % 2 == 1:
            break
        text = text[:-1]
    return text


def _segment_regex(segment: str) -> str:
    out: list[str] = []
    index = 0
    while index < len(segment):
        character = segment[index]
        if character == "*":
            out.append("[^/]*")
            index += 1
        elif character == "?":
            out.append("[^/]")
            index += 1
        elif character == "[":
            close = segment.find("]", index + 1)
            if close == -1:
                raise PatternError(
                    f"{segment!r} opens a character class and never closes it: "
                    "a stray '[' is a pattern nobody can read"
                )
            body = segment[index + 1 : close]
            if body.startswith("!"):
                body = "^" + body[1:]
            out.append("[" + body + "]")
            index = close + 1
        elif character == "\\" and index + 1 < len(segment):
            out.append(re.escape(segment[index + 1]))
            index += 2
        else:
            out.append(re.escape(character))
            index += 1
    return "".join(out)


def _path_regex(pattern: str) -> str:
    segments = pattern.split("/")
    pieces: list[str] = []
    for index, segment in enumerate(segments):
        last = index == len(segments) - 1
        if segment == "**":
            if index == 0:
                pieces.append(".*" if last else "(?:.*/)?")
            elif last:
                pieces.append("/.*")
            else:
                pieces.append("/(?:.*/)?")
            continue
        body = _segment_regex(segment)
        if index == 0 or segments[index - 1] == "**":
            pieces.append(body)
        else:
            pieces.append("/" + body)
    return "".join(pieces)


@dataclass(frozen=True)
class Rule:
    """One line of an ignore file, read once and kept whole.

    ``text`` is the line as written (minus behaviour-neutral padding), so an
    error message can quote it; ``body`` is the path pattern the regex was
    built from, with the ``!``, the trailing slash and the escaped prefix
    already accounted for.
    """

    text: str
    body: str
    line: int
    negated: bool
    dir_only: bool
    anchored: bool
    regex: re.Pattern[str]

    def matches(self, path: str, *, is_dir: bool) -> bool:
        if self.dir_only and not is_dir:
            return False
        return self.regex.match(path) is not None

    def render(self) -> str:
        return self.text


def parse_rule(line: str, number: int) -> Rule | None:
    text = _unescape_trailing_spaces(line)
    trimmed = text
    if not text:
        return None
    if text.startswith("#"):
        return None
    negated = False
    if text.startswith("\\!"):
        text = text[1:]
    elif text.startswith("!"):
        negated = True
        text = text[1:]
    if text.startswith("\\#"):
        text = text[1:]
    if not text:
        raise PatternError(f"line {number} is a bare '!': it negates nothing")
    dir_only = text.endswith("/")
    if dir_only:
        text = text.rstrip("/")
    if not text:
        raise PatternError(f"line {number} is a bare '/': it names no path")
    anchored = "/" in text
    body = _path_regex(text.lstrip("/") if anchored else text)
    expression = "^" + body + "$" if anchored else "^(?:.*/)?" + body + "$"
    try:
        compiled = re.compile(expression)
    except re.error as error:
        raise PatternError(f"line {number} cannot be compiled: {error}") from error
    return Rule(trimmed, text, number, negated, dir_only, anchored, compiled)


def parse_rules(lines: list[str]) -> list[Rule]:
    rules: list[Rule] = []
    for number, line in enumerate(lines, start=1):
        rule = parse_rule(line.rstrip("\r\n"), number)
        if rule is not None:
            rules.append(rule)
    if not rules:
        raise PatternError("the ignore file holds no rules")
    return rules
