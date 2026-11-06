"""Known answers for the merge, checked without pytest.

Every check here is a statement someone could disagree with. The point is that
the statements are cheap to read, so a reader can decide whether the merge is
right without reading the merge.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from . import cli as cli_module
from . import demo as demo_module
from .change import Change, changes
from .merge import DIFF3, MERGE, MergeError, merge_text

FIXTURES = Path(__file__).resolve().parent.parent.parent / "fixtures"


@dataclass
class Report:
    checks: int = 0
    failed: int = 0
    lines: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.failed == 0

    def section(self, name: str) -> None:
        self.lines.append(name)

    def equal(self, claim: str, got: object, expected: object) -> None:
        self.checks += 1
        if got == expected:
            self.lines.append(f"  ok   {claim}")
        else:
            self.failed += 1
            self.lines.append(f"  FAIL {claim}: {got!r} != {expected!r}")

    def check(self, claim: str, condition: bool) -> None:
        self.equal(claim, condition, True)

    def refuses(self, claim: str, error: type[Exception], call, *args, **kwargs) -> None:
        self.checks += 1
        try:
            call(*args, **kwargs)
        except error as caught:
            self.lines.append(f"  ok   {claim} ({caught})")
        except Exception as caught:
            self.failed += 1
            self.lines.append(
                f"  FAIL {claim}: raised {type(caught).__name__}, not {error.__name__}"
            )
        else:
            self.failed += 1
            self.lines.append(f"  FAIL {claim}: nothing was refused")

    def render(self) -> str:
        return (
            "\n".join(self.lines)
            + f"\nselftest: {self.checks - self.failed} checks passed, {self.failed} failed"
        )


def _changes(report: Report) -> None:
    report.section("changes")
    base = "a\nb\nc\n"
    found = changes(base, "a\nB\nc\n")
    report.equal("one replacement is one change", len(found), 1)
    report.equal("the change covers the edited line", (found[0].start, found[0].end), (1, 2))
    report.equal("its text is the new line", found[0].lines, ("B\n",))
    report.check("nothing changed means no changes", changes(base, base) == [])

    inserted = changes(base, "a\nx\nb\nc\n")
    report.check("an insertion consumes no base line", inserted[0].inserted)
    deleted = changes(base, "a\nc\n")
    report.check("a deletion contributes no lines", deleted[0].deleted)
    report.equal("a deletion still spans its base lines", deleted[0].replaced, 1)

    repeated = "".join(f"row {index}\n" for index in range(120))
    edited = repeated.replace("row 60\n", "row 60 edited\n")
    report.equal(
        "autojunk off: one edit in a repetitive file is one change",
        len(changes(repeated, edited)),
        1,
    )


def _overlaps(report: Report) -> None:
    report.section("overlaps")
    report.check("overlapping replacements touch", Change(2, 5, ()).touches(Change(4, 6, ())))
    report.check(
        "adjacent replacements do not touch", not Change(2, 3, ()).touches(Change(3, 4, ()))
    )
    report.check(
        "insertions at one point touch", Change(3, 3, ("x",)).touches(Change(3, 3, ("y",)))
    )
    report.check(
        "insertions at different points do not", not Change(3, 3, ()).touches(Change(4, 4, ()))
    )
    report.check(
        "an insertion beside a replacement does not touch",
        not Change(3, 3, ()).touches(Change(3, 4, ())),
    )


def _merge(report: Report) -> None:
    report.section("merge")
    base = "a\nb\nc\nd\n"
    untouched = merge_text(base, base, base)
    report.equal("an untouched file is the file", untouched.text, base)
    report.equal("and it has one chunk", len(untouched.chunks), 1)

    apart = merge_text(base, "a\nB\nc\nd\n", "a\nb\nc\nD\n")
    report.equal("edits in different places both land", apart.text, "a\nB\nc\nD\n")
    report.equal("with no conflict", apart.conflicts, 0)
    report.equal(
        "and four chunks",
        [chunk.kind for chunk in apart.chunks],
        ["same", "ours", "same", "theirs"],
    )

    same_edit = merge_text(base, "a\nB\nc\nd\n", "a\nB\nc\nd\n")
    report.equal("the same edit twice is not a conflict", same_edit.conflicts, 0)
    report.equal("it is counted as agreed", same_edit.agreed, 1)
    report.equal("and it appears once", same_edit.text.count("B"), 1)

    both_insert = merge_text(base, "a\nx\nb\nc\nd\n", "a\ny\nb\nc\nd\n")
    report.equal("two insertions at one point conflict", both_insert.conflicts, 1)
    report.check("both insertions are kept", "x" in both_insert.text and "y" in both_insert.text)

    boundary = merge_text(base, "a\nx\nb\nc\nd\n", "a\nB\nc\nd\n")
    report.equal("an insertion at a replaced line does not conflict", boundary.conflicts, 0)
    report.equal("the insertion lands before the replacement", boundary.text, "a\nx\nB\nc\nd\n")

    deletions = merge_text(base, "a\nb\nc\n", "b\nc\nd\n")
    report.equal("two deletions both apply", deletions.text, "b\nc\n")
    report.equal("and they do not conflict", deletions.conflicts, 0)

    report.equal(
        "unchanged ours gives theirs exactly",
        merge_text(base, base, "a\nB\nc\nD\n").text,
        "a\nB\nc\nD\n",
    )
    report.equal(
        "unchanged theirs gives ours exactly",
        merge_text(base, "A\nb\nC\nd\n", base).text,
        "A\nb\nC\nd\n",
    )

    ours, theirs = "a\nB\nc\nd\n", "a\nZ\nc\nd\n"
    report.equal(
        "swapping the sides keeps the conflict count",
        merge_text(base, ours, theirs).conflicts,
        merge_text(base, theirs, ours).conflicts,
    )
    report.equal(
        "a summary names the conflicts",
        merge_text(base, ours, theirs).summary().endswith("1 conflict(s)"),
        True,
    )


def _markers(report: Report) -> None:
    report.section("markers")
    base = "a\nb\nc\n"
    result = merge_text(base, "a\nB\nc\n", "a\nZ\nc\n", labels=("feature", "main"))
    report.check("the ours label is used", "<<<<<<< feature\n" in result.text)
    report.check("the theirs label is used", ">>>>>>> main\n" in result.text)
    report.check("ours comes first", result.text.index("B") < result.text.index("Z"))

    diff3 = merge_text(base, "a\nB\nc\n", "a\nZ\nc\n", style=DIFF3)
    report.check("diff3 keeps the base", "||||||| base\nb\n" in diff3.text)
    report.check(
        "the merge style never writes it",
        "|||||||" not in merge_text(base, "a\nB\nc\n", "a\nZ\nc\n").text,
    )

    unterminated = merge_text("a\nb", "a\nB", "a\nZ")
    report.equal(
        "a span without a final newline still leaves the marker alone on its line",
        unterminated.text,
        "a\n<<<<<<< ours\nB\n=======\nZ\n>>>>>>> theirs\n",
    )

    report.refuses(
        "an unknown style is refused", MergeError, merge_text, base, base, base, style="squash"
    )
    report.refuses(
        "an empty label is refused", MergeError, merge_text, base, base, base, labels=("ours", "")
    )
    report.refuses(
        "a label with a newline is refused",
        MergeError,
        merge_text,
        base,
        base,
        base,
        labels=("a\nb", "theirs"),
    )


def _empty(report: Report) -> None:
    report.section("empty files")
    report.equal("an empty base takes one side's text", merge_text("", "", "new\n").text, "new\n")
    report.equal("that is not a conflict", merge_text("", "", "new\n").conflicts, 0)
    report.equal(
        "two different texts on an empty base conflict", merge_text("", "x\n", "y\n").conflicts, 1
    )
    report.equal(
        "two identical texts on an empty base are agreed", merge_text("", "x\n", "x\n").agreed, 1
    )


def _fixtures(report: Report) -> None:
    report.section("fixtures")
    base = (FIXTURES / "base.txt").read_text(encoding="utf-8")
    ours = (FIXTURES / "ours.txt").read_text(encoding="utf-8")
    theirs = (FIXTURES / "theirs.txt").read_text(encoding="utf-8")
    result = merge_text(base, ours, theirs)
    report.equal("the fixture conflict is one conflict", result.conflicts, 1)
    report.check("the replicas change survived", "replicas: 4" in result.text)
    report.check("the image change survived", "image: checkout:1.5.0" in result.text)
    report.check(
        "the debug level is in dispute",
        "level: debug" in result.text and "level: warn" in result.text,
    )

    clean_base = (FIXTURES / "clean-base.txt").read_text(encoding="utf-8")
    clean_ours = (FIXTURES / "clean-ours.txt").read_text(encoding="utf-8")
    clean_theirs = (FIXTURES / "clean-theirs.txt").read_text(encoding="utf-8")
    clean = merge_text(clean_base, clean_ours, clean_theirs)
    report.equal("the clean fixture has no conflict", clean.conflicts, 0)
    report.check("the version bump survived", "## 1.5.0" in clean.text)
    report.check("the new bullet survived", "- webhooks" in clean.text)


def _stories(report: Report) -> None:
    report.section("stories")
    found = demo_module.stories()
    report.equal("six stories", len(found), 6)
    report.check("every story holds", all(story.held for story in found))
    report.equal(
        "and the footer says so", demo_module.render_stories(found)[-1], "stories      6 of 6 hold"
    )


def _command_line(report: Report) -> None:
    report.section("command line")
    parser = cli_module.build_parser()
    report.check(
        "merge routes to merge",
        parser.parse_args(["merge", "--base", "b", "--ours", "o", "--theirs", "t"]).handler
        is cli_module._command_merge,
    )
    report.check(
        "explain routes to explain",
        parser.parse_args(["explain", "--base", "b", "--ours", "o", "--theirs", "t"]).handler
        is cli_module._command_explain,
    )
    report.check(
        "demo routes to demo", parser.parse_args(["demo"]).handler is cli_module._command_demo
    )
    report.check(
        "selftest routes to selftest",
        parser.parse_args(["selftest"]).handler is cli_module._command_selftest,
    )
    report.equal(
        "the program name is set",
        cli_module.PROGRAM,
        "{{ npm_name }}",
    )
    report.equal(
        "the exit codes are distinct",
        (cli_module.EXIT_OK, cli_module.EXIT_CONFLICT, cli_module.EXIT_UNUSABLE),
        (0, 1, 2),
    )
    report.equal("the marker styles are the two we document", cli_module.STYLES, (MERGE, DIFF3))


def main() -> int:
    report = Report()
    for section in (
        _changes,
        _overlaps,
        _merge,
        _markers,
        _empty,
        _fixtures,
        _stories,
        _command_line,
    ):
        section(report)
    print(report.render())
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
