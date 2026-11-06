"""Patterns, and the segments they compile to.

A pattern is a promise about the shape of a path. ``/users/{id}`` promises
exactly two segments, the first of which is the word ``users``. ``*rest``
promises the rest of the path, whatever that turns out to be. Nothing here
guesses: a pattern that could be read two ways is refused when it is
registered, not when a request arrives.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

PARAM_NAME = re.compile(r"^[a-z_][a-z0-9_]*$")

STATIC = "static"
PARAM = "param"
CATCHALL = "catchall"
KINDS = (STATIC, PARAM, CATCHALL)


class PatternError(ValueError):
    """A pattern that cannot be compiled into an unambiguous shape."""


@dataclass(frozen=True)
class Segment:
    """One slash-separated piece of a pattern."""

    kind: str
    text: str

    @property
    def name(self) -> str:
        """The parameter name, for a parameter or a catch-all."""
        if self.kind == STATIC:
            raise PatternError(f"{self.text!r} is a literal, and a literal has no name")
        return self.text

    def render(self) -> str:
        if self.kind == STATIC:
            return self.text
        if self.kind == PARAM:
            return "{" + self.text + "}"
        return "*" + self.text


@dataclass(frozen=True)
class Pattern:
    """A compiled path pattern."""

    text: str
    segments: tuple[Segment, ...]

    @property
    def params(self) -> tuple[str, ...]:
        return tuple(s.name for s in self.segments if s.kind != STATIC)

    @property
    def catchall(self) -> str | None:
        for segment in self.segments:
            if segment.kind == CATCHALL:
                return segment.name
        return None

    @property
    def depth(self) -> int:
        """The number of segments a path must have, counting the catch-all as one."""
        return len(self.segments)

    def shape(self) -> str:
        return " ".join(kind for kind in (s.kind for s in self.segments)) or "(root)"

    def render(self) -> str:
        return "/" + "/".join(segment.render() for segment in self.segments)


def split_path(text: str) -> tuple[str, ...]:
    """Split a request path into segments, the same way a pattern is split.

    An empty path is the root. A trailing slash is a real empty segment, and
    it is refused rather than folded, because a router that folds it cannot
    tell ``/a`` and ``/a/`` apart and pretending otherwise hides a bug in the
    caller.
    """
    if not text.startswith("/"):
        raise PatternError(f"the path {text!r} does not start with '/', so it is not a path")
    if text == "/":
        return ()
    body = text[1:]
    if body.endswith("/"):
        raise PatternError(
            f"the path {text!r} has a trailing slash, and an empty last segment "
            "is not the same path as one without it; normalise before routing"
        )
    pieces = body.split("/")
    if not all(pieces):
        raise PatternError(f"the path {text!r} has an empty segment, which no route can name")
    return tuple(pieces)


def _parse_segment(raw: str, position: int) -> Segment:
    if raw.startswith("{") and raw.endswith("}") and len(raw) > 2:
        name = raw[1:-1]
        if "{" in name or "}" in name:
            raise PatternError(f"segment {position} ({raw!r}) has a brace inside a parameter name")
        if not PARAM_NAME.match(name):
            raise PatternError(
                f"segment {position} ({raw!r}) is not a parameter name; "
                "a name starts with a letter and holds letters, digits and underscores"
            )
        return Segment(PARAM, name)
    if raw.startswith("*"):
        name = raw[1:] or "rest"
        if not PARAM_NAME.match(name):
            raise PatternError(f"segment {position} ({raw!r}) is not a catch-all name")
        return Segment(CATCHALL, name)
    if "{" in raw or "}" in raw or "*" in raw:
        raise PatternError(
            f"segment {position} ({raw!r}) mixes a literal with a wildcard; "
            "a segment is either a literal, a whole parameter or a whole catch-all"
        )
    if not raw:
        raise PatternError(f"segment {position} is empty, and an empty segment names nothing")
    return Segment(STATIC, raw)


def parse_pattern(text: str) -> Pattern:
    """Compile a pattern, refusing anything that could be read two ways."""
    if not text:
        raise PatternError("a pattern cannot be empty; the root of a service is '/'")
    if not text.startswith("/"):
        raise PatternError(f"the pattern {text!r} does not start with '/', so it is not a path")
    segments = tuple(_parse_segment(raw, index) for index, raw in enumerate(split_path(text)))
    names = [segment.name for segment in segments if segment.kind != STATIC]
    duplicated = sorted({name for name in names if names.count(name) > 1})
    if duplicated:
        raise PatternError(
            f"the pattern {text!r} names {duplicated[0]!r} twice, and one name "
            "cannot hold two segments"
        )
    for index, segment in enumerate(segments):
        if segment.kind == CATCHALL and index != len(segments) - 1:
            raise PatternError(
                f"the catch-all in {text!r} is segment {index + 1} of {len(segments)}; "
                "a catch-all takes the rest of the path, so nothing can follow it"
            )
    return Pattern(text=text, segments=segments)


def render_path(segments: tuple[Segment, ...]) -> str:
    return "/" + "/".join(segment.render() for segment in segments) or "/"
