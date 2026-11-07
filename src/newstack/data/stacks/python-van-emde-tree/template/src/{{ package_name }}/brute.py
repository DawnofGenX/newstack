"""The oracles: a plain sort and two honest scans.

Every answer the tree gives must equal what this module answers on
the same keys. The successor is the first seat at or after the query
in a sorted list; the predecessor is the last seat at or before it;
membership is plain list membership. No cluster arithmetic anywhere,
so the tree cannot grade its own homework.

```text
cluster arithmetic pays the seek only when the scan agrees.
```
"""

from __future__ import annotations

from typing import Any


def brute_sort(keys: Any) -> list[int]:
    """The keys in plain sorted order, the answer every walk owes."""
    return sorted(keys)


def scan_successor(live: Any, key: int) -> int | None:
    """The smallest live seat >= key, found by scanning the sort."""
    for candidate in sorted(live):
        if candidate >= key:
            return candidate
    return None


def scan_predecessor(live: Any, key: int) -> int | None:
    """The largest live seat <= key, found by scanning the sort."""
    found: int | None = None
    for candidate in sorted(live):
        if candidate <= key:
            found = candidate
        else:
            break
    return found


def scan_member(live: Any, key: int) -> bool:
    """Plain membership, the answer `member` owes."""
    return key in list(live)
