"""Checks this build against the claims it makes, through the public surface."""

from __future__ import annotations

import io
from contextlib import redirect_stdout
from pathlib import Path

from . import cli as cli_module
from .demo import render_stories
from .pattern import PARAM, PatternError, parse_pattern, split_path
from .router import MATCH, NO_MATCH, NOT_ALLOWED, Router, RouterError

FIXTURES = Path(__file__).resolve().parent.parent.parent / "fixtures"


class Report:
    def __init__(self) -> None:
        self.checks = 0
        self.failed = 0
        self.lines: list[str] = []

    def section(self, title: str) -> None:
        self.lines.append(f"\n{title}")

    def ok(self, claim: str, held: bool) -> None:
        self.checks += 1
        if not held:
            self.failed += 1
        self.lines.append(f"  {'ok  ' if held else 'FAIL'} {claim}")

    def equal(self, claim: str, got, want) -> None:
        self.ok(f"{claim} (wanted {want!r}, got {got!r})" if got != want else claim, got == want)

    def refuses(self, claim: str, kind, call, needle: str) -> None:
        try:
            call()
        except kind as error:
            message = f"{claim} ({error})" if needle in str(error) else f"{claim}: {error}"
            self.ok(message, needle in str(error))
        except Exception as error:  # a wrong exception type is the failure
            self.ok(f"{claim}: raised {type(error).__name__} instead ({error})", False)
        else:
            self.ok(f"{claim}: no error raised", False)

    def render(self) -> list[str]:
        if self.failed:
            summary = f"\nselftest: {self.checks - self.failed} checks passed, {self.failed} failed"
        else:
            summary = f"\nselftest: {self.checks} checks passed, 0 failed"
        self.lines.append(summary)
        return self.lines


def _table() -> Router:
    router = Router()
    router.add("GET", "/", name="root")
    router.add("GET", "/users/me", name="me")
    router.add("GET", "/users/{id}", name="user")
    router.add("GET", "/users/{id}/posts", name="posts")
    router.add("POST", "/users/{id}/posts", name="create")
    router.add("DELETE", "/users/{id}", name="drop")
    router.add("GET", "/files/{name}", name="file")
    router.add("GET", "/files/*rest", name="tree")
    router.add("GET", "/a/b/d", name="static-only")
    router.add("GET", "/a/{x}/c", name="via-param")
    return router


def _patterns(report: Report) -> None:
    report.section("patterns")
    pattern = parse_pattern("/users/{id}/posts")
    report.equal("a pattern knows its depth", pattern.depth, 3)
    report.equal("a pattern lists its parameters", pattern.params, ("id",))
    report.equal("a parameter renders back with braces", pattern.render(), "/users/{id}/posts")
    report.equal("a catch-all renders with a star", parse_pattern("/f/*rest").render(), "/f/*rest")
    report.equal("an unnamed catch-all is called rest", parse_pattern("/f/*").params, ("rest",))
    report.equal("the root has no segments", parse_pattern("/").segments, ())
    report.equal("shape names each segment's kind", pattern.shape(), "static param static")
    report.equal("a segment knows its kind", pattern.segments[1].kind, PARAM)
    report.refuses(
        "a leading slash is required",
        PatternError,
        lambda: parse_pattern("users"),
        "does not start with '/'",
    )
    report.refuses(
        "a mixed segment is refused",
        PatternError,
        lambda: parse_pattern("/v{major}"),
        "mixes a literal with a wildcard",
    )
    report.refuses(
        "a catch-all in the middle is refused",
        PatternError,
        lambda: parse_pattern("/*all/end"),
        "nothing can follow it",
    )
    report.refuses(
        "a doubled name is refused",
        PatternError,
        lambda: parse_pattern("/{id}/{id}"),
        "names 'id' twice",
    )
    report.refuses(
        "an empty pattern is refused", PatternError, lambda: parse_pattern(""), "cannot be empty"
    )
    report.refuses(
        "an empty segment is refused", PatternError, lambda: parse_pattern("/a//b"), "empty segment"
    )
    report.refuses(
        "a trailing slash is refused in a pattern",
        PatternError,
        lambda: parse_pattern("/a/"),
        "trailing slash",
    )
    report.refuses(
        "a parameter name cannot start with a digit",
        PatternError,
        lambda: parse_pattern("/{1id}"),
        "not a parameter name",
    )
    report.equal("a request path splits the same way", split_path("/a/b"), ("a", "b"))
    report.equal("the root path has no segments", split_path("/"), ())
    report.refuses(
        "a request path needs a leading slash",
        PatternError,
        lambda: split_path("a/b"),
        "does not start with '/'",
    )


def _matching(report: Report) -> None:
    report.section("matching")
    router = _table()
    root = router.match("GET", "/")
    report.equal("the root matches the root", root.route.name, "root")
    report.equal("and binds nothing", root.params, ())
    me = router.match("GET", "/users/me")
    report.equal("a literal beats a parameter", me.route.name, "me")
    user = router.match("GET", "/users/42")
    report.equal("a parameter takes what is left", user.route.name, "user")
    report.equal("and binds the segment", user.param("id"), "42")
    nested = router.match("GET", "/users/42/posts")
    report.equal("a longer pattern wins by depth", nested.route.name, "posts")
    report.equal("the parameter keeps its value", dict(nested.params), {"id": "42"})
    near = router.match("GET", "/files/a.txt")
    report.equal("one segment goes to the parameter", near.route.name, "file")
    deep = router.match("GET", "/files/2026/11/a.txt")
    report.equal("many segments go to the catch-all", deep.route.name, "tree")
    report.equal("the catch-all keeps its slashes", deep.param("rest"), "2026/11/a.txt")
    report.equal("a match is a match", deep.kind, MATCH)
    report.equal("resolution exposes matched", deep.matched, True)


def _backtracking(report: Report) -> None:
    report.section("backtracking")
    router = _table()
    hit = router.match("GET", "/a/b/c")
    report.equal("a dead literal branch is abandoned", hit.route.name, "via-param")
    report.equal("and the parameter binds the segment that was tried", hit.param("x"), "b")
    miss = router.match("GET", "/a/b/x")
    report.equal("when no branch finishes it is a miss", miss.kind, NO_MATCH)
    report.ok("the reason names a segment", "segment" in miss.reason or "needs more" in miss.reason)
    both = Router()
    both.add("GET", "/a/{x}/c")
    both.add("GET", "/a/b/{y}")
    winner = both.match("GET", "/a/b/c").route.pattern.text
    report.equal("the literal at the first divergence wins", winner, "/a/b/{y}")
    report.equal(
        "and the parameter pattern takes the other path",
        both.match("GET", "/a/z/c").route.pattern.text,
        "/a/{x}/c",
    )
    one = Router()
    one.add("GET", "/a/{x}/c")
    one.add("GET", "/a/b/d")
    survivor = one.match("GET", "/a/b/c").route.pattern.text
    report.equal("a static dead end does not shadow a parameter", survivor, "/a/{x}/c")


def _methods(report: Report) -> None:
    report.section("methods")
    router = _table()
    wrong = router.match("DELETE", "/users/42/posts")
    report.equal("a wrong method is not a miss", wrong.kind, NOT_ALLOWED)
    report.equal("the allow list is every method that answers", wrong.allow, ("GET", "POST"))
    report.ok("and the reason says so", "another method" in wrong.reason)
    drop = router.match("DELETE", "/users/42")
    report.equal("a route registered for one method answers it", drop.route.name, "drop")
    report.equal(
        "HEAD is a method the router knows", router.match("HEAD", "/users/42").kind, NOT_ALLOWED
    )
    absent = router.match("GET", "/nothing/here")
    report.equal("an unknown path is a miss", absent.kind, NO_MATCH)
    report.equal("and offers no allow list", absent.allow, ())


def _refusals(report: Report) -> None:
    report.section("refusals")
    router = _table()
    report.refuses(
        "the same method and shape twice is refused",
        RouterError,
        lambda: router.add("GET", "/users/{other}"),
        "already registered",
    )
    report.refuses(
        "an unknown method is refused",
        RouterError,
        lambda: router.add("TRACE", "/x"),
        "not a method this router knows",
    )
    report.refuses(
        "an unknown method on a match is refused",
        RouterError,
        lambda: router.match("TRACE", "/"),
        "not a method this router knows",
    )
    report.refuses(
        "a request path with a trailing slash is refused",
        PatternError,
        lambda: router.match("GET", "/users/"),
        "trailing slash",
    )
    report.refuses(
        "an empty segment in a request is refused",
        PatternError,
        lambda: router.match("GET", "//users"),
        "empty segment",
    )
    posting = router.match("POST", "/users/42/posts").route.method
    report.equal("two routes may differ only by method", posting, "POST")


def _table_lines(report: Report) -> None:
    report.section("table")
    router = _table()
    report.equal("the table holds every route", len(router.routes), 10)
    lines = router.lines()
    report.equal("one line per route", len(lines), 10)
    has_method = any("GET" in line and "/users/me" in line for line in lines)
    report.ok("a line carries the method and the pattern", has_method)
    report.ok("a line carries the shape", any("static param" in line for line in lines))


def _fixtures(report: Report) -> None:
    report.section("fixtures")
    path = FIXTURES / "routes.txt"
    report.ok("the fixture table exists", path.is_file())
    if not path.is_file():
        return
    router = cli_module.load_routes(str(path))
    report.ok("the fixture compiles", len(router.routes) >= 6)
    literal = router.match("GET", "/users/me")
    report.equal("the fixture serves /users/me", literal.route.pattern.text, "/users/me")
    report.equal(
        "the fixture serves /users/7 from a parameter",
        router.match("GET", "/users/7").param("id"),
        "7",
    )
    report.equal(
        "the fixture refuses a method it does not route",
        router.match("PATCH", "/users/7").kind,
        NOT_ALLOWED,
    )


def _stories(report: Report) -> None:
    report.section("stories")
    lines = render_stories()
    report.equal("every story holds", lines[-1], "stories      6 of 6 hold")
    report.ok("no story prints a failure", not any("FAIL" in line for line in lines))


def _command_line(report: Report) -> None:
    report.section("command line")
    parser = cli_module.build_parser()
    parsed = parser.parse_args(["match", "--routes", "x", "--path", "/"])
    report.ok("match routes to its handler", parsed.handler is cli_module._command_match)
    expected = "{{ npm_name }}"
    report.equal("the program name is set", cli_module.PROGRAM, expected)
    report.ok(
        "the exit codes are distinct",
        len({cli_module.EXIT_OK, cli_module.EXIT_NO_MATCH, cli_module.EXIT_UNUSABLE}) == 3,
    )
    report.refuses(
        "a missing route table is unusable",
        cli_module.UsageError,
        lambda: cli_module.load_routes("/nope/routes.txt"),
        "no such route table",
    )
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        code = cli_module.main(["demo"])
    report.equal("demo exits zero", code, 0)
    report.ok("demo prints the footer", "6 of 6 hold" in buffer.getvalue())


def run() -> int:
    report = Report()
    _patterns(report)
    _matching(report)
    _backtracking(report)
    _methods(report)
    _refusals(report)
    _table_lines(report)
    _fixtures(report)
    _stories(report)
    _command_line(report)
    lines = report.render()
    for line in lines:
        print(line)
    return cli_module.EXIT_OK if report.failed == 0 else cli_module.EXIT_NO_MATCH
