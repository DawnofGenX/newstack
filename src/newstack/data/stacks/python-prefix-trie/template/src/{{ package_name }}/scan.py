"""The scan is the oracle: one comparison per word, no structure at all.

Every answer the trie gives must equal what this module answers on the
same corpus. If a structure cannot beat a scan's honesty with its own
speed, the structure is a confession, and these functions are the
sentence it is compared against.
"""

from __future__ import annotations


def scan_has(words: list[str], word: str) -> bool:
    """Membership by walking the corpus once."""
    return any(held == word for held in words)


def scan_prefix(words: list[str], stem: str) -> list[str]:
    """The sorted listing of every corpus word that starts with the stem."""
    return sorted(word for word in words if word.startswith(stem))


def scan_lcp(words: list[str]) -> str:
    """The stem every corpus word shares, found by pairwise trimming."""
    if not words:
        return ""
    head = words[0]
    for word in words[1:]:
        limit = min(len(head), len(word))
        stop = 0
        while stop < limit and head[stop] == word[stop]:
            stop += 1
        head = head[:stop]
        if not head:
            break
    return head
