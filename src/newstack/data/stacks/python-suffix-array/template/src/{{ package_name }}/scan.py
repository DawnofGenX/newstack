"""The scan is the oracle: a sort by slicing, a count by starting points.

Every answer the table gives must equal what this module answers on
the same text. The order is `sorted(range(n), key=text[i:])` with no
cleverness at all; the count is one start position per match, overlaps
included. If rank doubling cannot beat the slice-sort's honesty with
its own speed, the table is a confession, and these functions are the
sentence it is compared against.
"""

from __future__ import annotations


def scan_array(text: str) -> list[int]:
    """The suffix starts, sorted by the plainest rule there is."""
    return sorted(range(len(text)), key=lambda at: text[at:])


def scan_count(text: str, pattern: str) -> int:
    """Every start where the pattern begins. Overlaps are counted.

    The rule this text owes: `text.count(pattern)` walks left to right
    and never restarts inside a match it already spent, so a pattern
    that overlaps itself is under-counted. The table counts every
    start position, so the scan is the truth and `str.count` is the
    shortcut that agrees whenever the pattern cannot overlap itself.
    """
    if not pattern:
        return 0
    return sum(1 for at in range(len(text)) if text.startswith(pattern, at))


def scan_lcp_pair(text: str, left: int, right: int) -> int:
    """The shared prefix of two suffixes, letters compared one by one."""
    if left == right:
        return len(text) - left
    limit = min(len(text) - left, len(text) - right)
    stop = 0
    while stop < limit and text[left + stop] == text[right + stop]:
        stop += 1
    return stop


def scan_lcp_array(text: str) -> list[int]:
    """Neighbour shares of the plain sort, one comparison per pair."""
    order = scan_array(text)
    return [
        scan_lcp_pair(text, order[k], order[k + 1]) for k in range(len(order) - 1)
    ]


def scan_lrs(text: str) -> str:
    """The longest repeated substring, found by the tallest neighbour share."""
    order = scan_array(text)
    shares = scan_lcp_array(text)
    if not shares:
        return ""
    best = max(shares)
    if best == 0:
        return ""
    start = order[shares.index(best)]
    return text[start : start + best]
