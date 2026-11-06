"""In-process checks: the rules, the anchors, the walks, and the command line."""

from __future__ import annotations

import io
import json
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from . import cli as cli_module
from . import demo as demo_module
from .matcher import Matcher, PathError
from .pattern import PatternError, parse_rule, parse_rules


class Report:
    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0

    def ok(self, name: str, condition: bool, detail: str = "") -> None:
        if condition:
            self.passed += 1
            print(f"ok   {name}")
        else:
            self.failed += 1
            print(f"FAIL {name}{': ' + detail if detail else ''}")

    def refuses(self, name: str, kind: type[BaseException], action) -> None:
        try:
            action()
        except kind:
            self.ok(name, True)
        except BaseException as error:
            self.ok(name, False, f"raised {type(error).__name__}: {error}")
        else:
            self.ok(name, False, "nothing was raised")


def _matcher(rules: list[str]) -> Matcher:
    matcher, _ = Matcher.from_lines(rules)
    return matcher


def _reading(report: Report) -> None:
    report.ok("a comment is not a rule", parse_rule("# build output", 1) is None)
    report.ok("a blank line is not a rule", parse_rule("   ", 2) is None)
    rule = parse_rule("!keep.log", 3)
    report.ok("a leading bang negates", rule is not None and rule.negated)
    report.ok("the line number is kept", rule is not None and rule.line == 3)
    escaped_bang = parse_rule("\\!important", 4)
    report.ok(
        "an escaped bang is a name, not a negation",
        escaped_bang is not None and not escaped_bang.negated and escaped_bang.body == "!important",
    )
    escaped_hash = parse_rule("\\#notes", 5)
    report.ok(
        "an escaped hash is a name, not a comment",
        escaped_hash is not None and escaped_hash.body == "#notes",
    )
    directory = parse_rule("build/", 6)
    report.ok("a trailing slash means directory only", directory is not None and directory.dir_only)
    report.ok(
        "the trailing slash stays in the text but not in the body",
        directory is not None and directory.text == "build/" and directory.body == "build",
    )
    rooted = parse_rule("/build", 7)
    report.ok("a leading slash anchors", rooted is not None and rooted.anchored)
    plain = parse_rule("build", 8)
    report.ok("a bare name is not anchored", plain is not None and not plain.anchored)
    nested = parse_rule("logs/*.log", 9)
    report.ok("a slash anywhere anchors", nested is not None and nested.anchored)
    padded = parse_rule("notes.txt   ", 10)
    report.ok(
        "trailing spaces are dropped",
        padded is not None and padded.text == "notes.txt",
    )
    protected = parse_rule("notes.txt\\ ", 11)
    report.ok(
        "a backslash protects a trailing space",
        protected is not None and protected.text == "notes.txt\\ ",
    )
    report.refuses("a bare bang is refused", PatternError, lambda: parse_rule("!", 12))
    report.refuses("a bare slash is refused", PatternError, lambda: parse_rule("/", 13))
    report.refuses("an unclosed class is refused", PatternError, lambda: parse_rule("file[0-9", 14))
    report.refuses("an empty rule set is refused", PatternError, lambda: parse_rules([]))
    report.ok(
        "comments and blanks are skipped but numbering is real",
        [rule.line for rule in parse_rules(["# a", "*.log", "", "!a.log"])] == [2, 4],
    )


def _globs(report: Report) -> None:
    star = _matcher(["*.log"])
    report.ok("a star matches a name", star.ignored("app.log"))
    report.ok("a star matches at any depth", star.ignored("logs/deep/app.log"))
    report.ok("a star does not become a slash", star.ignored("app.log.txt") is False)
    question = _matcher(["temp?.md"])
    report.ok("a question mark matches one character", question.ignored("tempA.md"))
    report.ok("a question mark needs one character", question.ignored("temp.md") is False)
    report.ok("a question mark does not match two", question.ignored("tempAB.md") is False)
    klass = _matcher(["file[0-9].txt"])
    report.ok("a class matches inside the range", klass.ignored("file7.txt"))
    report.ok("a class refuses outside the range", klass.ignored("filex.txt") is False)
    negated_class = _matcher(["file[!0-9].txt"])
    report.ok("a negated class flips the answer", negated_class.ignored("filex.txt"))
    report.ok("a negated class refuses digits", negated_class.ignored("file7.txt") is False)
    shallow = _matcher(["logs/*.log"])
    deep = _matcher(["logs/**/*.log"])
    report.ok("one star stops at the slash", shallow.ignored("logs/x/a.log") is False)
    report.ok("two stars cross the slash", deep.ignored("logs/x/a.log"))
    report.ok("two stars still match one level", deep.ignored("logs/a.log"))
    trailing = _matcher(["logs/**"])
    report.ok("a trailing two-star takes everything under", trailing.ignored("logs/x/y/a.log"))
    leading = _matcher(["**/cache"])
    report.ok("a leading two-star matches the root too", leading.ignored("cache"))


def _anchors(report: Report) -> None:
    bare = _matcher(["build"])
    rooted = _matcher(["/build"])
    report.ok("a bare name matches a nested directory", bare.ignored("sub/build", is_dir=True))
    report.ok("a rooted name does not", rooted.ignored("sub/build", is_dir=True) is False)
    report.ok("a rooted name matches at the root", rooted.ignored("build", is_dir=True))
    nested = _matcher(["src/*.pyc"])
    report.ok("a rule with a slash is anchored where it sits", nested.ignored("src/a.pyc"))
    report.ok("and it does not drift deeper", nested.ignored("x/src/a.pyc") is False)
    report.refuses("an empty path is refused", PathError, lambda: bare.decide(""))
    report.refuses("a dot-dot path is refused", PathError, lambda: bare.decide("../escape"))
    report.refuses("an empty segment is refused", PathError, lambda: bare.decide("a//b"))
    report.ok(
        "a leading ./ is stripped",
        bare.decide("./build", is_dir=True).path == "build",
    )


def _directories(report: Report) -> None:
    matcher = _matcher(["build/"])
    report.ok("a file named build survives", matcher.ignored("build") is False)
    report.ok("a directory named build is ignored", matcher.ignored("build", is_dir=True))
    verdict = matcher.decide("build/out/app.js")
    report.ok("its contents are ignored through the parent", verdict.ignored)
    report.ok("the parent is named", verdict.parent == "build")
    report.ok("the reason says why a negation would not help here", "parent" in verdict.reason)
    report.ok(
        "an ignored directory does not ignore a sibling with the same prefix",
        matcher.ignored("build-tools", is_dir=True) is False,
    )


def _negation(report: Report) -> None:
    matcher = _matcher(["*.log", "!keep.log"])
    report.ok("a later negation re-includes", matcher.ignored("keep.log") is False)
    report.ok("the general rule still holds", matcher.ignored("other.log"))
    reversed_matcher = _matcher(["!keep.log", "*.log"])
    report.ok("order matters", reversed_matcher.ignored("keep.log"))
    blocked = _matcher(["build/", "!build/keep.txt"])
    blocked_verdict = blocked.ignored("build/keep.txt")
    report.ok("a negation cannot rescue a file inside an excluded directory", blocked_verdict)
    reachable = _matcher(["build/*", "!build/keep.txt"])
    report.ok("a rule that names files can be undone", reachable.ignored("build/keep.txt") is False)
    report.ok(
        "the negation is the rule that decided",
        reachable.decide("build/keep.txt").rule is not None
        and reachable.decide("build/keep.txt").rule.negated,
    )
    none = _matcher(["*.log"])
    report.ok("no rule means tracked", none.ignored("main.py") is False)


def _walks(report: Report) -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        (root / "build").mkdir()
        (root / "build" / "out.js").write_text("x", encoding="utf-8")
        (root / "app.log").write_text("x", encoding="utf-8")
        (root / "main.py").write_text("x", encoding="utf-8")
        matcher = _matcher(["build/", "*.log"])
        verdicts = matcher.walk(root)
        ignored = sorted(verdict.path for verdict in verdicts if verdict.ignored)
        report.ok("the walk decides every path, directories included", len(verdicts) == 4)
        report.ok(
            "the walk skips nothing it should see",
            ignored == ["app.log", "build", "build/out.js"],
        )
        tracked = any(not verdict.ignored for verdict in verdicts)
        report.ok("a tracked file is still reported", tracked)
        report.refuses(
            "walking a file is refused", PathError, lambda: matcher.walk(root / "main.py")
        )


def _stories(report: Report) -> None:
    stories = demo_module.stories()
    report.ok("there are six stories", len(stories) == 6)
    for story in stories:
        report.ok(f"story {story.number} holds", story.held(), story.title)
    rendered = demo_module.render_stories()
    report.ok("the last line counts the stories", rendered[-1] == "stories      6 of 6 hold")


def _command_line(report: Report) -> None:
    parser = cli_module.build_parser()
    report.ok(
        "selftest routes to its handler",
        parser.parse_args(["selftest"]).handler is cli_module._command_selftest,
    )
    demo_handler = parser.parse_args(["demo"]).handler
    report.ok("demo routes to its handler", demo_handler is cli_module._command_demo)
    with tempfile.TemporaryDirectory() as raw:
        ignore = Path(raw) / ".gitignore"
        ignore.write_text("*.log\nbuild/\n!keep.log\n", encoding="utf-8")
        out = io.StringIO()
        with redirect_stdout(out):
            status = cli_module.main(["explain", "app.log", "--ignore", str(ignore)])
        report.ok("explain exits one for an ignored path", status == cli_module.EXIT_IGNORED)
        report.ok("explain says ignored", "verdict    ignored" in out.getvalue())
        with redirect_stdout(io.StringIO()):
            status = cli_module.main(["explain", "main.py", "--ignore", str(ignore)])
        report.ok("explain exits zero for a tracked path", status == cli_module.EXIT_OK)
        out = io.StringIO()
        with redirect_stdout(out):
            cli_module.main(["list", "--ignore", str(ignore), "--json"])
        payload = json.loads(out.getvalue())
        report.ok("list reports every rule", len(payload) == 3)
        report.ok("list marks the negation", payload[2]["negated"] is True)
        out = io.StringIO()
        with redirect_stdout(out):
            cli_module.main(["explain", "keep.log", "--ignore", str(ignore), "--json"])
        verdict = json.loads(out.getvalue())
        report.ok("the json verdict carries the rule", verdict["rule"] == "!keep.log")
        report.ok("the json verdict says tracked", verdict["ignored"] is False)
        err = io.StringIO()
        with redirect_stdout(io.StringIO()), redirect_stderr(err):
            status = cli_module.main(["explain", "a.log", "--ignore", str(Path(raw) / "absent")])
        report.ok("a missing ignore file is unusable", status == cli_module.EXIT_UNUSABLE)
        report.ok("the message names the file", "absent" in err.getvalue())


def run() -> int:
    report = Report()
    sections = (
        _reading,
        _globs,
        _anchors,
        _directories,
        _negation,
        _walks,
        _stories,
        _command_line,
    )
    for section in sections:
        section(report)
    total = report.passed + report.failed
    print(f"selftest: {report.passed} checks passed, {report.failed} failed")
    print(f"total    {total}")
    return 0 if report.failed == 0 else 1
