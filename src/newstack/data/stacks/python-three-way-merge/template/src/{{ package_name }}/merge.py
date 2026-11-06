"""Merge two edits of one base, and refuse to guess where they disagree.

A three-way merge has exactly one question to answer: for every region of the
base, what did each side do to it? When only one side touched a region the
answer is that side. When both touched it the answer is a conflict unless both
made the same edit. Everything else -- ordering insertions, picking a winner,
"smart" resolution -- is a guess dressed as a merge.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .change import Change, changes, split_lines

MERGE = "merge"
DIFF3 = "diff3"
STYLES = (MERGE, DIFF3)

SAME = "same"
OURS = "ours"
THEIRS = "theirs"
BOTH = "both"
CONFLICT = "conflict"


class MergeError(ValueError):
    """The merge cannot be attempted as asked."""


@dataclass(frozen=True)
class Chunk:
    """One region of the base and what the merge decided to do with it."""

    kind: str
    start: int
    end: int
    base: tuple[str, ...]
    ours: tuple[str, ...]
    theirs: tuple[str, ...]
    text: tuple[str, ...]

    def line(self, number: int) -> str:
        span = (
            f"base {self.start}..{self.end}" if self.start != self.end else f"base at {self.start}"
        )
        first = self.text[0].rstrip("\n") if self.text else ""
        detail = f"  first line {first!r}" if first else ""
        return f"{number:>2}  {self.kind:<8} {span:<14} {len(self.text):>2} line(s){detail}"


@dataclass(frozen=True)
class MergeResult:
    text: str
    chunks: tuple[Chunk, ...]
    ours_changes: tuple[Change, ...]
    theirs_changes: tuple[Change, ...]

    @property
    def conflicts(self) -> int:
        return sum(1 for chunk in self.chunks if chunk.kind == CONFLICT)

    @property
    def agreed(self) -> int:
        return sum(1 for chunk in self.chunks if chunk.kind == BOTH)

    @property
    def clean(self) -> bool:
        return self.conflicts == 0

    def lines(self) -> list[str]:
        return [chunk.line(number) for number, chunk in enumerate(self.chunks, 1)]

    def summary(self) -> str:
        return (
            f"chunks {len(self.chunks)}: {len(self.ours_changes)} change(s) from ours, "
            f"{len(self.theirs_changes)} from theirs, "
            f"{self.agreed} agreed, {self.conflicts} conflict(s)"
        )


def _apply(span: list[str], cluster: list[Change], start: int) -> list[str]:
    """The base span with one side's changes applied."""
    if not cluster:
        return list(span)
    out: list[str] = []
    cursor = 0
    for change in sorted(cluster, key=lambda item: (item.start, item.end)):
        out.extend(span[cursor : change.start - start])
        out.extend(change.lines)
        cursor = change.end - start
    out.extend(span[cursor:])
    return out


def _terminated(lines: list[str]) -> list[str]:
    """Markers must start on their own line, so a span without a final newline gets one."""
    if lines and not lines[-1].endswith("\n"):
        return [*lines[:-1], lines[-1] + "\n"]
    return list(lines)


def _conflict(
    base_span: list[str],
    ours_span: list[str],
    theirs_span: list[str],
    labels: tuple[str, str],
    style: str,
) -> list[str]:
    out = [f"<<<<<<< {labels[0]}\n"]
    out.extend(_terminated(ours_span))
    if style == DIFF3:
        out.append("||||||| base\n")
        out.extend(_terminated(base_span))
    out.append("=======\n")
    out.extend(_terminated(theirs_span))
    out.append(f">>>>>>> {labels[1]}\n")
    return out


def merge_text(
    base: str,
    ours: str,
    theirs: str,
    *,
    labels: tuple[str, str] = ("ours", "theirs"),
    style: str = MERGE,
) -> MergeResult:
    """Merge two edits of ``base``, writing conflict markers where they disagree."""
    if style not in STYLES:
        raise MergeError(f"{style!r} is not a marker style; use one of {', '.join(STYLES)}")
    for label in labels:
        if not label.strip():
            raise MergeError("a conflict label cannot be empty: the marker has to name a side")
        if "\n" in label:
            raise MergeError(f"a conflict label cannot contain a newline: {label!r}")

    base_lines = split_lines(base)
    ours_changes = changes(base_lines, split_lines(ours))
    theirs_changes = changes(base_lines, split_lines(theirs))

    chunks: list[Chunk] = []

    def same(start: int, end: int) -> None:
        if start == end:
            return
        span = tuple(base_lines[start:end])
        chunks.append(Chunk(SAME, start, end, span, span, span, span))

    def joins(change: Change, low: int, high: int, alongside: list[Change]) -> bool:
        """Does this change belong to the cluster [low, high)?

        A change that starts before the end of the span overlaps it. Two
        insertions at the very same point also belong together: neither
        consumes a base line, so nothing in the base orders them. An insertion
        that merely sits at the boundary does not join -- its position relative
        to the span is already decided by the base.
        """
        if change.start < high:
            return True
        return any(
            other.inserted and change.inserted and other.start == change.start
            for other in alongside
        )

    i = j = pos = 0
    while i < len(ours_changes) or j < len(theirs_changes):
        ours_next = (
            (ours_changes[i].start, ours_changes[i].end)
            if i < len(ours_changes)
            else (len(base_lines) + 1, 0)
        )
        theirs_next = (
            (theirs_changes[j].start, theirs_changes[j].end)
            if j < len(theirs_changes)
            else (len(base_lines) + 1, 0)
        )
        take_ours = ours_next <= theirs_next
        start = ours_next[0] if take_ours else theirs_next[0]
        same(pos, start)
        pos = start

        ours_cluster: list[Change] = []
        theirs_cluster: list[Change] = []
        if take_ours:
            ours_cluster.append(ours_changes[i])
            end = max(start, ours_changes[i].end)
            i += 1
        else:
            theirs_cluster.append(theirs_changes[j])
            end = max(start, theirs_changes[j].end)
            j += 1

        joined = True
        while joined:
            joined = False
            while i < len(ours_changes) and joins(ours_changes[i], start, end, theirs_cluster):
                ours_cluster.append(ours_changes[i])
                end = max(end, ours_changes[i].end)
                i += 1
                joined = True
            while j < len(theirs_changes) and joins(theirs_changes[j], start, end, ours_cluster):
                theirs_cluster.append(theirs_changes[j])
                end = max(end, theirs_changes[j].end)
                j += 1
                joined = True

        base_span = base_lines[start:end]
        ours_span = _apply(base_span, ours_cluster, start)
        theirs_span = _apply(base_span, theirs_cluster, start)
        if not theirs_cluster:
            chunks.append(
                Chunk(
                    OURS,
                    start,
                    end,
                    tuple(base_span),
                    tuple(ours_span),
                    tuple(theirs_span),
                    tuple(ours_span),
                )
            )
        elif not ours_cluster:
            chunks.append(
                Chunk(
                    THEIRS,
                    start,
                    end,
                    tuple(base_span),
                    tuple(ours_span),
                    tuple(theirs_span),
                    tuple(theirs_span),
                )
            )
        elif ours_span == theirs_span:
            chunks.append(
                Chunk(
                    BOTH,
                    start,
                    end,
                    tuple(base_span),
                    tuple(ours_span),
                    tuple(theirs_span),
                    tuple(ours_span),
                )
            )
        else:
            markers = _conflict(base_span, ours_span, theirs_span, labels, style)
            chunks.append(
                Chunk(
                    CONFLICT,
                    start,
                    end,
                    tuple(base_span),
                    tuple(ours_span),
                    tuple(theirs_span),
                    tuple(markers),
                )
            )
        pos = end

    same(pos, len(base_lines))

    text = "".join("".join(chunk.text) for chunk in chunks)
    return MergeResult(text, tuple(chunks), tuple(ours_changes), tuple(theirs_changes))


def merge_files(
    base_path: str | Path,
    ours_path: str | Path,
    theirs_path: str | Path,
    *,
    labels: tuple[str, str] = ("ours", "theirs"),
    style: str = MERGE,
) -> MergeResult:
    try:
        base = Path(base_path).read_text(encoding="utf-8")
        ours = Path(ours_path).read_text(encoding="utf-8")
        theirs = Path(theirs_path).read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise MergeError(f"a merge is on text, and one of these files is not: {error}") from error
    return merge_text(base, ours, theirs, labels=labels, style=style)
