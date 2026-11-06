"""Six merges, each printed with the claim it is making checked.

The point of the demo is not that a merge produced some text. It is that the
text is the answer to a question with a right answer, and each story says which
question it asked.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .merge import DIFF3, merge_text

BASE = """# Deploy notes

Plan:
- build
- test
- ship
- watch
"""


@dataclass
class Story:
    title: str
    lines: list[str] = field(default_factory=list)
    held: bool = True

    def say(self, text: str) -> None:
        self.lines.append(text)

    def require(self, claim: str, condition: bool) -> None:
        mark = "ok  " if condition else "FAIL"
        self.lines.append(f"  {mark} {claim}")
        self.held = self.held and condition

    def block(self, text: str) -> None:
        for line in text.splitlines():
            self.lines.append(f"    {line}")


def _story_one() -> Story:
    story = Story("two edits in different places merge without a marker")
    ours = BASE.replace("- test\n", "- test --coverage\n")
    theirs = BASE + "- rollback\n"
    result = merge_text(BASE, ours, theirs)
    story.say("ours changes the test line, theirs appends a rollback line.")
    story.block(result.text)
    story.require("no conflict", result.conflicts == 0)
    story.require("the coverage flag survived", "- test --coverage" in result.text)
    story.require("the appended line survived", result.text.endswith("- rollback\n"))
    story.require(
        "both edits are counted", len(result.ours_changes) + len(result.theirs_changes) == 2
    )
    return story


def _story_two() -> Story:
    story = Story("the same edit on both sides is not a conflict")
    same = BASE.replace("- ship\n", "- ship --verify\n")
    result = merge_text(BASE, same, same)
    story.say("both sides made the identical change, so there is nothing to decide.")
    story.block(result.text)
    story.require("no conflict", result.conflicts == 0)
    story.require("the chunk is marked as agreed", result.agreed == 1)
    story.require("the line appears once", result.text.count("- ship --verify") == 1)
    story.require("nothing else moved", result.text.count("\n") == BASE.count("\n"))
    return story


def _story_three() -> Story:
    story = Story("two insertions at the same point have no order, so they conflict")
    ours = BASE.replace("- build\n", "- build\n- lint\n")
    theirs = BASE.replace("- build\n", "- build\n- fmt\n")
    result = merge_text(BASE, ours, theirs)
    story.say("each side adds a line directly after - build. Either order is defensible.")
    story.block(result.text)
    story.require("one conflict", result.conflicts == 1)
    story.require("ours is inside the markers", "<<<<<<< ours\n- lint\n=======\n" in result.text)
    story.require("theirs is inside the markers", "=======\n- fmt\n>>>>>>> theirs\n" in result.text)
    story.require("the disputed point holds only the two insertions", result.chunks[1].base == ())
    return story


def _story_four() -> Story:
    story = Story("a conflict is local: the rest of the file is still merged")
    ours = BASE.replace("- test\n", "- test --coverage\n")
    theirs = BASE.replace("- test\n", "- test --parallel\n")
    result = merge_text(BASE, ours, theirs)
    story.say("both sides rewrote the same line; only that line is in dispute.")
    story.block(result.text)
    story.require("one conflict", result.conflicts == 1)
    story.require(
        "the header is outside the markers",
        result.text.startswith("# Deploy notes\n\nPlan:\n- build\n"),
    )
    story.require("the tail is outside the markers", result.text.endswith("- ship\n- watch\n"))
    story.require(
        "the disputed line is inside them",
        "--coverage" in result.text and "--parallel" in result.text,
    )
    story.require(
        "three chunks: same, conflict, same",
        [chunk.kind for chunk in result.chunks] == ["same", "conflict", "same"],
    )
    return story


def _story_five() -> Story:
    story = Story("diff3 markers keep the base, so the reader can see both edits")
    ours = BASE.replace("- ship\n", "- ship --verify\n")
    theirs = BASE.replace("- ship\n", "- ship --dry-run\n")
    result = merge_text(BASE, ours, theirs, style=DIFF3)
    story.say("the base section is what each side started from.")
    story.block(result.text)
    story.require("one conflict", result.conflicts == 1)
    story.require("the base marker is present", "||||||| base\n- ship\n" in result.text)
    story.require(
        "the merge style never writes it", "|||||||" not in merge_text(BASE, ours, theirs).text
    )
    return story


def _story_six() -> Story:
    story = Story("deletions merge like any other change")
    ours = BASE.replace("- watch\n", "")
    theirs = BASE.replace("- build\n", "")
    result = merge_text(BASE, ours, theirs)
    story.say("each side removed a different line.")
    story.block(result.text)
    story.require("no conflict", result.conflicts == 0)
    story.require("the watch line is gone", "- watch" not in result.text)
    story.require("the build line is gone", "- build" not in result.text)
    both = merge_text(BASE, ours, ours)
    story.require("the same deletion twice is agreed", both.conflicts == 0 and both.agreed == 1)
    return story


def stories() -> list[Story]:
    return [
        _story_one(),
        _story_two(),
        _story_three(),
        _story_four(),
        _story_five(),
        _story_six(),
    ]


def render_stories(found: list[Story] | None = None) -> list[str]:
    found = stories() if found is None else found
    out: list[str] = []
    for number, story in enumerate(found, 1):
        out.append(f"{number}. {story.title}")
        out.extend(story.lines)
        out.append("")
    total = len(found)
    holding = sum(1 for story in found if story.held)
    out.append(
        f"stories      {holding} of {total} hold"
        if holding == total
        else f"stories      BROKEN: {holding} of {total} hold"
    )
    return out


def main() -> int:
    for line in render_stories():
        print(line)
    return 0 if all(story.held for story in stories()) else 1
