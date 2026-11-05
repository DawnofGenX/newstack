"""Fit a parsed patch onto a text, and refuse when the fit is a guess."""

from __future__ import annotations

from dataclasses import dataclass

from .model import ApplyError, FilePatch, Hunk, shown, split_lines


@dataclass(frozen=True)
class Applied:
    """The result of a patch, plus what the tool had to tolerate to get there."""

    text: str
    fuzz: tuple[tuple[int, int], ...]

    @property
    def fuzzy(self) -> bool:
        return bool(self.fuzz)

    def line(self) -> str:
        if not self.fuzz:
            return "applied   clean"
        parts = [f"hunk {index} dropped {count}" for index, count in self.fuzz]
        return "applied   with fuzz: " + ", ".join(parts)


def apply_text(original: str, patch: FilePatch, *, fuzz: int = 0) -> Applied:
    """Apply every hunk in order, remeasuring each one against the text it lands on."""
    if fuzz < 0:
        raise ApplyError(f"fuzz must not be negative, got {fuzz}")
    old = split_lines(original)
    out: list[str] = []
    cursor = 0
    used: list[tuple[int, int]] = []
    for number, hunk in enumerate(patch.hunks, 1):
        if hunk.old_start < cursor + 1 and hunk.old_count:
            raise ApplyError(
                f"hunk {number} starts at line {hunk.old_start}, before line {cursor + 1} "
                "where the previous hunk ended; the patch is out of order"
            )
        position, lead, level = _locate(old, hunk, cursor, fuzz, number)
        if level:
            used.append((number, level))
        trail = _trail(hunk, level)
        end = position + len(hunk.old_lines) - lead - trail
        # Everything before the core comes from the file, including context that fuzz
        # let us stop comparing: a tolerated line is kept as the file has it, not as the
        # patch remembers it.
        out.extend(old[cursor:position])
        out.extend(hunk.new_lines[lead : len(hunk.new_lines) - trail])
        out.extend(old[end : end + trail])
        cursor = end + trail
    out.extend(old[cursor:])
    return Applied("".join(out), tuple(used))


def _trail(hunk: Hunk, level: int) -> int:
    return min(level, hunk.trailing_context)


def _locate(
    old: list[str], hunk: Hunk, cursor: int, fuzz: int, number: int
) -> tuple[int, int, int]:
    """Find where the hunk's surviving core lands; return (position, dropped, level)."""
    need = hunk.old_lines
    expected = hunk.old_start - 1 if hunk.old_count else hunk.old_start
    for level in range(fuzz + 1):
        lead = min(level, hunk.leading_context)
        trail = min(level, hunk.trailing_context)
        core = need[lead : len(need) - trail]
        if not core:
            return max(cursor, min(expected + lead, len(old))), lead, level
        want = expected + lead
        if _same(old, want, core):
            return want, lead, level
        spots = _find(old, core, cursor)
        if len(spots) == 1:
            return spots[0], lead, level
        if len(spots) > 1:
            first, second = spots[0] + 1, spots[1] + 1
            raise ApplyError(
                f"hunk {number} matches at lines {first} and {second}: the patch does not "
                "say which one, and guessing would corrupt one of them"
            )
    raise ApplyError(_mismatch(old, need, expected, number))


def _same(old: list[str], start: int, core: list[str]) -> bool:
    if start < 0 or start + len(core) > len(old):
        return False
    return old[start : start + len(core)] == core


def _find(old: list[str], core: list[str], cursor: int) -> list[int]:
    return [start for start in range(cursor, len(old) - len(core) + 1)
            if old[start : start + len(core)] == core]


def _mismatch(old: list[str], need: list[str], expected: int, number: int) -> str:
    if not old:
        return f"hunk {number} does not apply: the file is empty and the patch expects " \
               f"{shown(need[0])} at line 1"
    for offset, want in enumerate(need):
        at = expected + offset
        if at >= len(old):
            return (f"hunk {number} does not apply: the patch expects {len(need)} line(s) "
                    f"at line {expected + 1}, but the text ends after {len(old)}")
        if old[at] != want:
            return (f"hunk {number} does not apply: line {at + 1} is {shown(old[at])}, "
                    f"the patch expects {shown(want)}")
    return f"hunk {number} does not apply"
