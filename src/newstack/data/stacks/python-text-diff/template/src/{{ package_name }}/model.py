"""The vocabulary of a unified diff: lines, hunks, and what a patch claims."""

from __future__ import annotations

from dataclasses import dataclass

CONTEXT = 3
NO_NEWLINE = r"\ No newline at end of file"
KINDS = (" ", "-", "+")


class DiffError(ValueError):
    """Base class for every refusal this tool makes."""


class ParseError(DiffError):
    """A patch is malformed: it does not say what it claims to do."""


class ApplyError(DiffError):
    """A patch is well formed, but it does not fit this text."""


def split_lines(text: str) -> list[str]:
    """Split keeping line endings, so "a\\n" and "a" stay different lines."""
    return text.splitlines(keepends=True)


def shown(line: str) -> str:
    """A line as an error message shows it, with the ending made visible."""
    if line.endswith("\n"):
        return repr(line[:-1])
    return f"{line!r} without a trailing newline"


def _range(start: int, count: int) -> str:
    """A hunk range in the format patch(1) reads: the count is omitted when it is 1."""
    return str(start) if count == 1 else f"{start},{count}"


@dataclass(frozen=True)
class Hunk:
    """One block of the patch: a range on each side, and the lines in between."""

    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: tuple[tuple[str, str], ...]
    section: str = ""

    @property
    def old_lines(self) -> list[str]:
        return [text for kind, text in self.lines if kind in (" ", "-")]

    @property
    def new_lines(self) -> list[str]:
        return [text for kind, text in self.lines if kind in (" ", "+")]

    @property
    def leading_context(self) -> int:
        count = 0
        for kind, _text in self.lines:
            if kind != " ":
                break
            count += 1
        return count

    @property
    def trailing_context(self) -> int:
        count = 0
        for kind, _text in reversed(self.lines):
            if kind != " ":
                break
            count += 1
        return count

    def header(self) -> str:
        head = f"@@ -{_range(self.old_start, self.old_count)}"
        head += f" +{_range(self.new_start, self.new_count)} @@"
        return f"{head} {self.section}" if self.section else head

    def line(self) -> str:
        removed = sum(1 for kind, _ in self.lines if kind == "-")
        added = sum(1 for kind, _ in self.lines if kind == "+")
        return (
            f"hunk {self.old_start:>4} -{removed:<3} +{added:<3} "
            f"{self.old_count:>3} old / {self.new_count:>3} new line(s)"
        )


@dataclass(frozen=True)
class FilePatch:
    """One file's patch: two path headers and the hunks, in order."""

    old_path: str
    new_path: str
    hunks: tuple[Hunk, ...]

    @property
    def added(self) -> int:
        return sum(1 for hunk in self.hunks for kind, _ in hunk.lines if kind == "+")

    @property
    def removed(self) -> int:
        return sum(1 for hunk in self.hunks for kind, _ in hunk.lines if kind == "-")

    def line(self) -> str:
        return (
            f"{self.old_path} -> {self.new_path}: {len(self.hunks)} hunk(s), "
            f"+{self.added} -{self.removed}"
        )
