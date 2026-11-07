"""Six stories about suffixes, starts, and what a table owes its text.

Every number printed here is computed at run time by the real modules;
a story that stops holding fails the selftest, not the reader.
"""

from __future__ import annotations

from dataclasses import dataclass

from .corpus import synthetic
from .scan import scan_array, scan_count, scan_lcp_pair, scan_lrs
from .suffix import SuffixArray


@dataclass(frozen=True)
class Story:
    """One claim, the numbers behind it, and whether it held."""

    title: str
    detail: str
    held: bool


def stories() -> list[Story]:
    """The six claims the table makes, each computed fresh."""
    corpus = synthetic(60, seed=9)
    text = "".join(corpus[:6])
    table = SuffixArray(text)

    ordered = table.array == scan_array(text)
    first = Story(
        "the order is the plain sort, exactly",
        f"{len(text)} starts, slice-equal={ordered}",
        ordered and table.invariant(),
    )

    patterns = [text[:2], "aa", text[7:10], "zzz"]
    honest = all(table.count(p) == scan_count(text, p) for p in patterns)
    second = Story(
        "the count is every start, overlaps honest",
        f"{len(patterns)} patterns, scan-equal={honest}, "
        f"'aa'={table.count('aa')} vs str.count {text.count('aa')}"
        if len(text) > 9
        else f"{len(patterns)} patterns, scan-equal={honest}",
        honest,
    )

    lcp_ok = all(
        table.lcp(a, b) == scan_lcp_pair(text, a, b)
        for a, b in ((0, 1), (3, 3), (5, min(9, len(text) - 1)))
        if b < len(text)
    )
    third = Story(
        "two suffixes share what the scan compares",
        f"probes on a {len(text)}-letter text, scan-equal={lcp_ok}",
        lcp_ok,
    )

    shares = table.lcp_array()
    repeat = table.longest_repeat()
    fourth = Story(
        "the longest repeat is the tallest share",
        f"repeat={repeat!r} of {len(shares)} neighbour shares, "
        f"height={max(shares, default=0)}",
        repeat == scan_lrs(text) and len(shares) == max(len(text) - 1, 0),
    )

    storm_ok = all(
        SuffixArray(body).array == scan_array(body) for body in corpus[:20]
    )
    fifth = Story(
        "seeded texts order the way slices sort",
        f"20 of {len(corpus)} corpora, slice-equal={storm_ok}",
        storm_ok,
    )

    edges = [
        SuffixArray("").array == [],
        SuffixArray("a").array == [0],
        SuffixArray("a").lcp_array() == [],
        SuffixArray("aa").longest_repeat() == "a",
    ]
    sixth = Story(
        "empty and single letters answer without complaint",
        f"edge probes held={all(edges)}",
        all(edges),
    )
    return [first, second, third, fourth, fifth, sixth]
