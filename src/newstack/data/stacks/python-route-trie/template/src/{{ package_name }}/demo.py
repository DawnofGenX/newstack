"""Six stories about routing, each with its own check."""

from __future__ import annotations

from .pattern import PatternError
from .router import NO_MATCH, NOT_ALLOWED, Router, RouterError


class Story:
    def __init__(self, title: str) -> None:
        self.title = title
        self.lines: list[str] = []
        self.checks: list[tuple[str, bool]] = []

    def say(self, line: str) -> None:
        self.lines.append(line)

    def block(self, text: str) -> None:
        for line in text.strip("\n").split("\n"):
            self.lines.append("  " + line)

    def require(self, claim: str, held: bool) -> None:
        self.checks.append((claim, bool(held)))

    @property
    def held(self) -> bool:
        return all(held for _, held in self.checks)


def _table() -> Router:
    router = Router()
    router.add("GET", "/users/me", name="me")
    router.add("GET", "/users/{id}", name="user")
    router.add("GET", "/users/{id}/posts", name="posts")
    router.add("POST", "/users/{id}/posts", name="create-post")
    router.add("GET", "/files/{name}", name="file")
    router.add("GET", "/files/*rest", name="file-tree")
    router.add("GET", "/a/{x}/c", name="deep-param")
    router.add("GET", "/a/b/{y}", name="deep-static")
    return router


def _story_one(router: Router, story: Story) -> None:
    hit = router.match("GET", "/users/me")
    other = router.match("GET", "/users/42")
    story.block(f"/users/me  -> {hit.route.name}\n/users/42  -> {other.route.name}")
    story.require("the literal route wins for its own word", hit.route.name == "me")
    story.require("the parameter route takes everything else", other.route.name == "user")
    story.require("and it binds the segment it consumed", other.param("id") == "42")


def _story_two(router: Router, story: Story) -> None:
    near = router.match("GET", "/files/notes.txt")
    deep = router.match("GET", "/files/2026/11/notes.txt")
    one = f"/files/notes.txt            -> {near.route.name}"
    many = f"/files/2026/11/notes.txt    -> {deep.route.name}"
    story.block(one + "\n" + many)
    story.require("one segment goes to the parameter", near.route.name == "file")
    story.require("more segments go to the catch-all", deep.route.name == "file-tree")
    story.require("the catch-all keeps the slashes", deep.param("rest") == "2026/11/notes.txt")


def _story_three(story: Story) -> None:
    router = Router()
    router.add("GET", "/a/b/d", name="static-only")
    router.add("GET", "/a/{x}/c", name="param")
    story.block(
        "/a/b/d and /a/{x}/c are registered.\n"
        "For /a/b/c the literal 'b' branch cannot continue, so the matcher backs out\n"
        "and tries the parameter branch instead of reporting a miss."
    )
    hit = router.match("GET", "/a/b/c")
    story.block(f"/a/b/c  -> {hit.route.name}, {dict(hit.params)}")
    story.require("the parameter branch is still reachable", hit.route.name == "param")
    story.require("and it keeps its own name for the value", hit.param("x") == "b")


def _story_four(router: Router, story: Story) -> None:
    hit = router.match("GET", "/a/b/c")
    story.block(
        "/a/{x}/c and /a/b/{y} both match /a/b/c.\n"
        "Segment 2 decides: 'b' is a literal in the second, a parameter in the first."
    )
    story.block(f"winner     {hit.route.name}")
    story.require("the literal at segment 2 wins", hit.route.name == "deep-static")
    story.require("so the value lands in the second pattern's name", hit.param("y") == "c")


def _story_five(router: Router, story: Story) -> None:
    wrong = router.match("DELETE", "/users/42/posts")
    absent = router.match("GET", "/users/42/comments")
    story.block(
        f"DELETE /users/42/posts   -> {wrong.kind}, allow {', '.join(wrong.allow)}\n"
        f"GET    /users/42/comments -> {absent.kind}"
    )
    story.block(f"reason  {absent.reason}")
    story.require("a known path with a wrong method says so", wrong.kind == NOT_ALLOWED)
    story.require("and lists the methods that would work", wrong.allow == ("GET", "POST"))
    story.require("a path nobody registered is a miss", absent.kind == NO_MATCH)
    story.require("with a reason that names the segment", "'comments'" in absent.reason)


def _story_six(router: Router, story: Story) -> None:
    refused = ""
    try:
        router.match("GET", "/users/42/")
    except PatternError as error:
        refused = str(error)
    story.block(f"/users/42/  refused: {refused}")
    story.require("the request path is refused, not quietly fixed", "trailing slash" in refused)
    clash = ""
    try:
        router.add("GET", "/users/{id}")
    except RouterError as error:
        clash = str(error)
    shape = "GET /users/" + "{" + "id" + "}"
    story.block(f"adding {shape} twice: {clash}")
    story.require("a second route on one shape is refused", "already registered" in clash)
    story.require("and the refusal names the route that holds it", "GET /users/{id}" in clash)


def stories() -> list[Story]:
    parts = [
        Story("1. a literal beats a parameter"),
        Story("2. a parameter beats a catch-all"),
        Story("3. a dead branch is abandoned"),
        Story("4. the first divergence decides"),
        Story("5. a wrong method is not a missing resource"),
        Story("6. a trailing slash is a different path"),
    ]
    _story_one(_table(), parts[0])
    _story_two(_table(), parts[1])
    _story_three(parts[2])
    _story_four(_table(), parts[3])
    _story_five(_table(), parts[4])
    _story_six(_table(), parts[5])
    return parts


def render_stories() -> list[str]:
    lines: list[str] = []
    parts = stories()
    for story in parts:
        lines.append(story.title)
        lines.extend(story.lines)
        for claim, held in story.checks:
            lines.append(f"  {'ok  ' if held else 'FAIL'} {claim}")
        lines.append("")
    held = sum(1 for story in parts if story.held)
    total = len(parts)
    if held == total:
        lines.append(f"stories      {held} of {total} hold")
    else:
        lines.append(f"stories      BROKEN {held} of {total}")
    return lines
