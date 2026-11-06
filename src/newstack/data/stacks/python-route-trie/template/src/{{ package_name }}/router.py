"""A trie of paths, matched segment by segment.

The rule that makes a router predictable is short: at every segment, a literal
beats a parameter, and a parameter beats a catch-all. The rule that makes it
correct is the other half: if a branch cannot finish, the matcher goes back and
tries the looser branch, so a route is never missed because a more specific one
happened to share a prefix.

Nothing here folds a trailing slash, sorts routes by how many wildcards they
carry, or picks the "best" of several matches after the fact. Matching is a
walk, and the walk's order is the rule.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .pattern import (
    PARAM,
    STATIC,
    Pattern,
    parse_pattern,
    split_path,
)

METHODS = ("GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS")

MATCH = "match"
NO_MATCH = "no-match"
NOT_ALLOWED = "not-allowed"


class RouterError(ValueError):
    """A route that cannot be registered."""


@dataclass(frozen=True)
class Route:
    """One method on one pattern."""

    method: str
    pattern: Pattern
    name: str = ""

    @property
    def text(self) -> str:
        return f"{self.method} {self.pattern.text}"

    def line(self) -> str:
        return f"{self.method:<7} {self.pattern.text:<34} {self.pattern.shape()}"


@dataclass
class _Node:
    """One position in the trie. Parameter and catch-all slots are shared."""

    static: dict[str, _Node] = field(default_factory=dict)
    param: _Node | None = None
    catchall: _Node | None = None
    routes: dict[str, Route] = field(default_factory=dict)

    def methods(self) -> tuple[str, ...]:
        return tuple(sorted(self.routes))


@dataclass(frozen=True)
class Resolution:
    """What happened to one request, and why."""

    kind: str
    method: str
    path: str
    route: Route | None = None
    params: tuple[tuple[str, str], ...] = ()
    allow: tuple[str, ...] = ()
    reason: str = ""

    @property
    def matched(self) -> bool:
        return self.kind == MATCH

    def param(self, name: str) -> str:
        for key, value in self.params:
            if key == name:
                return value
        raise KeyError(name)

    def as_dict(self) -> dict:
        payload: dict = {"kind": self.kind, "method": self.method, "path": self.path}
        if self.route is not None:
            payload["route"] = self.route.text
            payload["name"] = self.route.name
        payload["params"] = dict(self.params)
        if self.allow:
            payload["allow"] = list(self.allow)
        if self.reason:
            payload["reason"] = self.reason
        return payload


def _bind(pattern: Pattern, segments: tuple[str, ...]) -> list[tuple[str, str]]:
    """Read the parameter values out of a path that the walk already accepted."""
    bound: list[tuple[str, str]] = []
    for index, piece in enumerate(pattern.segments):
        if piece.kind == STATIC:
            continue
        if piece.kind == PARAM:
            bound.append((piece.name, segments[index]))
            continue
        rest = "/".join(segments[index:])
        bound.append((piece.name, rest))
    return bound


class Router:
    """A table of routes that answers with a route, or with a reason."""

    def __init__(self) -> None:
        self._root = _Node()

    # -- registration --------------------------------------------------
    def add(self, method: str, pattern: str, *, name: str = "") -> Route:
        return self.add_route(Route(method=method, pattern=parse_pattern(pattern), name=name))

    def add_route(self, route: Route) -> Route:
        if route.method not in METHODS:
            raise RouterError(
                f"{route.method!r} is not a method this router knows; it knows {', '.join(METHODS)}"
            )
        node = self._root
        for segment in route.pattern.segments:
            if segment.kind == STATIC:
                node = node.static.setdefault(segment.text, _Node())
            elif segment.kind == PARAM:
                if node.param is None:
                    node.param = _Node()
                node = node.param
            else:
                if node.catchall is None:
                    node.catchall = _Node()
                node = node.catchall
        existing = node.routes.get(route.method)
        if existing is not None:
            raise RouterError(
                f"{route.method} {route.pattern.text} is already registered as {existing.text!r}; "
                "two routes cannot own one shape and method"
            )
        node.routes[route.method] = route
        return route

    def add_all(self, routes) -> None:
        for route in routes:
            self.add_route(route)

    @property
    def routes(self) -> list[Route]:
        found: list[Route] = []

        def walk(node: _Node) -> None:
            found.extend(node.routes.values())
            for child in node.static.values():
                walk(child)
            if node.param is not None:
                walk(node.param)
            if node.catchall is not None:
                walk(node.catchall)

        walk(self._root)
        return sorted(found, key=lambda route: (route.pattern.text, route.method))

    def lines(self) -> list[str]:
        return [route.line() for route in self.routes]

    # -- matching ------------------------------------------------------
    def match(self, method: str, path: str) -> Resolution:
        if method not in METHODS:
            raise RouterError(
                f"{method!r} is not a method this router knows; it knows {', '.join(METHODS)}"
            )
        segments = split_path(path)
        notes: list[str] = []
        found = self._walk(self._root, segments, method, 0, path, notes)
        if found is not None:
            route, bound = found
            return Resolution(
                kind=MATCH, method=method, path=path, route=route, params=tuple(bound)
            )
        allowed = self._allowed(self._root, segments, 0)
        if allowed:
            return Resolution(
                kind=NOT_ALLOWED,
                method=method,
                path=path,
                allow=allowed,
                reason=(
                    f"the path matches {len(allowed)} route(s) for another method, "
                    f"so this is {', '.join(allowed)} and not a missing resource"
                ),
            )
        reason = notes[0] if notes else "no route in this table has this shape"
        return Resolution(kind=NO_MATCH, method=method, path=path, reason=reason)

    def _walk(
        self,
        node: _Node,
        segments: tuple[str, ...],
        method: str,
        index: int,
        path: str,
        notes: list[str],
    ) -> tuple[Route, list[tuple[str, str]]] | None:
        if index == len(segments):
            route = node.routes.get(method)
            if route is not None:
                return route, _bind(route.pattern, segments)
            if node.routes:
                notes.append(
                    f"the path ends here and the routes at this point answer "
                    f"{', '.join(node.methods())}, not {method}"
                )
            else:
                notes.append(
                    f"the path has {len(segments)} segment(s) and the deepest route "
                    f"under {'/' if not segments else '/' + '/'.join(segments)} needs more"
                )
            return None
        piece = segments[index]
        child = node.static.get(piece)
        if child is not None:
            found = self._walk(child, segments, method, index + 1, path, notes)
            if found is not None:
                return found
        if node.param is not None:
            found = self._walk(node.param, segments, method, index + 1, path, notes)
            if found is not None:
                return found
        if node.catchall is not None:
            route = node.catchall.routes.get(method)
            if route is not None:
                return route, _bind(route.pattern, segments)
            if node.catchall.routes:
                notes.append(
                    f"the catch-all here answers {', '.join(node.catchall.methods())}, not {method}"
                )
        known = sorted(node.static)
        if not known and node.param is None and node.catchall is None:
            notes.append(
                f"segment {index + 1} of the path is {piece!r}, and no route continues from here"
            )
        elif node.static and piece not in node.static:
            options = ", ".join(repr(word) for word in known[:3])
            more = "" if len(known) <= 3 else f" and {len(known) - 3} more"
            notes.append(
                f"segment {index + 1} of the path is {piece!r}, and the literals here are "
                f"{options}{more}"
            )
        return None

    def _allowed(self, node: _Node, segments: tuple[str, ...], index: int) -> tuple[str, ...]:
        """Every method that answers this shape, ignoring which method was asked for."""
        if index == len(segments):
            return node.methods()
        found: list[str] = []
        piece = segments[index]
        child = node.static.get(piece)
        if child is not None:
            found.extend(self._allowed(child, segments, index + 1))
        if node.param is not None:
            found.extend(self._allowed(node.param, segments, index + 1))
        if node.catchall is not None:
            found.extend(node.catchall.methods())
        return tuple(sorted(set(found)))
