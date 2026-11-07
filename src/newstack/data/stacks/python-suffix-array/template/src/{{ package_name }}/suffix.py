"""The table itself: sorted suffix starts, honest O(n log^2 n).

A suffix is the text from one letter to the end, and the table is
those starts in sorted order — the same order a plain
`sorted(range(n), key=text[i:])` would answer with, reached by rank
doubling instead of slicing. The build is honest about its cost: a
sort per doubling round over log n rounds. Counting scans forward
from a binary-search entry; the LCP array pairs table neighbours; the
longest repeat is the tallest neighbour share.
"""

from __future__ import annotations

from bisect import bisect_left

from .text import ensure_pattern, ensure_text


class SuffixError(ValueError):
    """The table was asked about a place it does not hold."""


def _pair_lcp(text: str, left: int, right: int) -> int:
    """Letters two suffixes share, compared one letter at a time."""
    if left == right:
        return len(text) - left
    limit = min(len(text) - left, len(text) - right)
    stop = 0
    while stop < limit and text[left + stop] == text[right + stop]:
        stop += 1
    return stop


def _rank_order(text: str) -> list[int]:
    """Suffix starts in sorted order, by rank doubling, no slicing sort.

    Each round sorts every start by the pair (rank here, rank a `width`
    away) and re-ranks; a doubling of `width` per round over log n
    rounds keeps the whole build at O(n log^2 n) comparisons, and every
    round's answer is checked against the plain sort in the selftest.
    """
    size = len(text)
    order = list(range(size))
    if size <= 1:
        return order
    rank = [ord(char) for char in text]
    width = 1
    while width < size:
        order.sort(
            key=lambda at: (rank[at], rank[at + width] if at + width < size else -1)
        )
        fresh = [0] * size
        for step in range(1, size):
            before, here = order[step - 1], order[step]
            before_key = (
                rank[before],
                rank[before + width] if before + width < size else -1,
            )
            here_key = (rank[here], rank[here + width] if here + width < size else -1)
            fresh[here] = fresh[before] + (before_key != here_key)
        rank = fresh
        if rank[order[-1]] == size - 1:
            break
        width *= 2
    return order


class SuffixArray:
    """Sorted suffix starts of one text, and the questions they answer.

    The count rule this text owes, written plain: occurrences are
    counted per start position, so a pattern that overlaps itself is
    counted at every start — `str.count` restarts after each match it
    spent and under-counts those, and the table follows the scan.
    """

    def __init__(self, text: str) -> None:
        self.text = ensure_text(text)
        self._order = _rank_order(self.text)
        self._rank = [-1] * len(self.text)
        for place, start in enumerate(self._order):
            self._rank[start] = place

    def __len__(self) -> int:
        return len(self._order)

    @property
    def array(self) -> list[int]:
        """The starts, in table (lexicographic) order."""
        return list(self._order)

    def suffix_at(self, start: int) -> str:
        """The text from one letter to the end."""
        if not 0 <= start < len(self.text):
            raise SuffixError(f"no suffix starts at {start}")
        return self.text[start:]

    def count(self, pattern: str) -> int:
        """Every start where the pattern begins, found by binary search."""
        return len(self._window(ensure_pattern(pattern)))

    def positions(self, pattern: str) -> list[int]:
        """Starts holding the pattern, in table order, overlaps honest."""
        return list(self._window(ensure_pattern(pattern)))

    def _window(self, wanted: str) -> list[int]:
        """The table slice of starts whose suffix opens with the pattern.

        A binary search lands on the first suffix at or past the
        pattern; the answer is the run from there while the suffix
        still opens with it. Returning the entry point without the
        scan is the mutation this class exists to refuse.
        """
        entry = bisect_left(self._order, wanted, key=lambda at: self.text[at:])
        found: list[int] = []
        place = entry
        while place < len(self._order) and self.text.startswith(
            wanted, self._order[place]
        ):
            found.append(self._order[place])
            place += 1
        return found

    def lcp_array(self) -> list[int]:
        """Shares between table neighbours, in table order."""
        return [
            _pair_lcp(self.text, self._order[place], self._order[place + 1])
            for place in range(len(self._order) - 1)
        ]

    def lcp(self, left: int, right: int) -> int:
        """Letters two suffixes share, through the rank range between."""
        if not 0 <= left < len(self.text) or not 0 <= right < len(self.text):
            raise SuffixError(f"no suffix at {left} or {right}")
        if left == right:
            return len(self.text) - left
        low, high = sorted((self._rank[left], self._rank[right]))
        shares = self.lcp_array()
        return min(shares[low:high])

    def longest_repeat(self) -> str:
        """The longest text repeated at two starts: the tallest share."""
        shares = self.lcp_array()
        if not shares:
            return ""
        tallest = max(shares)
        if tallest == 0:
            return ""
        start = self._order[shares.index(tallest)]
        return self.text[start : start + tallest]

    def invariant(self) -> bool:
        """The table holds its own shape: starts, shares, order."""
        size = len(self.text)
        if sorted(self._order) != list(range(size)):
            return False
        if len(self.lcp_array()) != max(size - 1, 0):
            return False
        return all(
            self.text[self._order[place] :] <= self.text[self._order[place + 1] :]
            for place in range(len(self._order) - 1)
        )

    def audit(self) -> list[str]:
        """Complaints about the table, empty when the table is seated."""
        complaints: list[str] = []
        size = len(self.text)
        if sorted(self._order) != list(range(size)):
            complaints.append("the starts are not the positions once each")
        for place in range(len(self._order) - 1):
            left = self.text[self._order[place] :]
            right = self.text[self._order[place + 1] :]
            if left > right:
                complaints.append(f"neighbours {place} and {place + 1} are out of order")
        return complaints


def build(text: str) -> SuffixArray:
    """The table over validated text; the empty text gets an empty table."""
    return SuffixArray(text)
