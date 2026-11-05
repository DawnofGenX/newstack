"""Turn two texts into hunks, and hunks into the text patch(1) reads."""

from __future__ import annotations

from difflib import SequenceMatcher

from .model import (
    CONTEXT,
    NO_NEWLINE,
    ApplyError,
    FilePatch,
    Hunk,
    ParseError,
    split_lines,
)


def diff_lines(old: list[str], new: list[str], context: int = CONTEXT) -> list[Hunk]:
    """Group the changed regions of two line lists into hunks with context."""
    if context < 0:
        raise ApplyError(f"context must not be negative, got {context}")
    matcher = SequenceMatcher(None, old, new, autojunk=False)
    hunks: list[Hunk] = []
    for group in matcher.get_grouped_opcodes(context):
        if not group:
            continue
        first, last = group[0], group[-1]
        old_count, new_count = last[2] - first[1], last[4] - first[3]
        # Opcode indices are 0-based; a unified header is 1-based, except that an empty
        # range names the line it is inserted AFTER, which makes `@@ -0,0 +1 @@` the
        # header for "the first line of a file that had none".
        old_start = first[1] + 1 if old_count else first[1]
        new_start = first[3] + 1 if new_count else first[3]
        lines: list[tuple[str, str]] = []
        for tag, i1, i2, j1, j2 in group:
            if tag == "equal":
                lines.extend((" ", line) for line in old[i1:i2])
            elif tag == "delete":
                lines.extend(("-", line) for line in old[i1:i2])
            elif tag == "insert":
                lines.extend(("+", line) for line in new[j1:j2])
            else:
                lines.extend(("-", line) for line in old[i1:i2])
                lines.extend(("+", line) for line in new[j1:j2])
        hunks.append(Hunk(old_start, old_count, new_start, new_count,
                          tuple(_mark_newlines(lines))))
    return hunks


def _mark_newlines(lines: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Insert the "no newline at end of file" marker after any line that lacks one.

    Only the last line of a file can lack a newline, so a marker anywhere else is a
    patch written by hand, and parse_patch rejects those.
    """
    marked: list[tuple[str, str]] = []
    for kind, text in lines:
        marked.append((kind, text))
        if not text.endswith("\n"):
            marked.append(("\\", NO_NEWLINE))
    return marked


def diff_text(old: str, new: str, context: int = CONTEXT) -> FilePatch:
    """Diff two whole texts, header paths included."""
    return FilePatch("old", "new", tuple(diff_lines(split_lines(old), split_lines(new),
                                                    context)))


def format_patch(patch: FilePatch) -> str:
    """Render a patch exactly as patch(1) expects to read it."""
    out = [f"--- {patch.old_path}\n", f"+++ {patch.new_path}\n"]
    for hunk in patch.hunks:
        out.append(hunk.header() + "\n")
        for kind, text in hunk.lines:
            if kind == "\\":
                if out[-1] and not out[-1].endswith("\n"):
                    out.append("\n")
                out.append(NO_NEWLINE + "\n")
            else:
                out.append(kind + text)
    return "".join(out)


def parse_patch(text: str) -> FilePatch:
    """Read a unified diff back into hunks, refusing anything malformed."""
    raw = text.split("\n")
    if raw and raw[-1] == "":
        raw.pop()
    lines = [line + "\n" for line in raw]
    old_path = new_path = None
    hunks: list[Hunk] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.startswith("--- "):
            if hunks or old_path is not None:
                raise ParseError("this tool applies one file per patch; a second --- header "
                                 "was found")
            old_path = _path_of(line)
            index += 1
            if index >= len(lines) or not lines[index].startswith("+++ "):
                raise ParseError("the --- header is not followed by a +++ header")
            new_path = _path_of(lines[index])
            index += 1
            continue
        if line.startswith("@@ "):
            if old_path is None:
                raise ParseError("a hunk appears before the --- and +++ headers")
            hunk, index = _read_hunk(lines, index, len(hunks) + 1)
            hunks.append(hunk)
            continue
        if line.startswith("\\") or line.strip() == "":
            index += 1
            continue
        index += 1
    if old_path is None or new_path is None:
        raise ParseError("no --- and +++ headers: this is not a unified diff")
    if not hunks:
        raise ParseError("the patch has headers but no hunks")
    return FilePatch(old_path, new_path, tuple(hunks))


def _path_of(line: str) -> str:
    name = line[4:].rstrip("\n").split("\t")[0].strip()
    return name


def _read_hunk(lines: list[str], index: int, number: int) -> tuple[Hunk, int]:
    header = lines[index][3:].rstrip("\n")
    section = ""
    if "@@" in header:
        body, section = header.split("@@", 1)
    else:
        body = header
    parts = body.split()
    if len(parts) != 2 or not parts[0].startswith("-") or not parts[1].startswith("+"):
        raise ParseError(f"hunk {number}: cannot read the header {header!r}")
    old_start, old_count = _span(parts[0][1:], number)
    new_start, new_count = _span(parts[1][1:], number)
    body_lines: list[tuple[str, str]] = []
    index += 1
    while index < len(lines) and not lines[index].startswith("@@ "):
        if lines[index].startswith("--- ") and body_lines:
            break
        text = lines[index]
        if text.startswith("\\"):
            _check_marker(body_lines, number)
            body_lines.append(("\\", text.rstrip("\n")))
        elif text.startswith((" ", "-", "+")):
            body_lines.append((text[0], text[1:]))
        elif text.rstrip("\n") == "":
            body_lines.append((" ", "\n"))
        else:
            raise ParseError(f"hunk {number}: {text.rstrip()!r} is not a diff line")
        index += 1
    old_seen = [kind for kind, _ in body_lines if kind in (" ", "-")]
    new_seen = [kind for kind, _ in body_lines if kind in (" ", "+")]
    if len(old_seen) != old_count:
        raise ParseError(f"hunk {number}: the header claims {old_count} old line(s) but "
                         f"the body has {len(old_seen)}")
    if len(new_seen) != new_count:
        raise ParseError(f"hunk {number}: the header claims {new_count} new line(s) but "
                         f"the body has {len(new_seen)}")
    hunk = Hunk(old_start, old_count, new_start, new_count, tuple(body_lines), section.strip())
    return hunk, index


def _check_marker(body_lines: list[tuple[str, str]], number: int) -> None:
    """Take the newline off the line before a marker: that is what the marker means."""
    if not body_lines:
        raise ParseError(f"hunk {number}: a no-newline marker with no line before it")
    kind, text = body_lines[-1]
    if not text.endswith("\n"):
        raise ParseError(f"hunk {number}: two no-newline markers in a row")
    body_lines[-1] = (kind, text[:-1])


def _span(text: str, number: int) -> tuple[int, int]:
    pieces = text.split(",")
    try:
        start = int(pieces[0])
        count = int(pieces[1]) if len(pieces) > 1 else 1
    except ValueError:
        raise ParseError(f"hunk {number}: {text!r} is not a line range") from None
    if count < 0 or start < 0:
        raise ParseError(f"hunk {number}: {text!r} has a negative number")
    return start, count
