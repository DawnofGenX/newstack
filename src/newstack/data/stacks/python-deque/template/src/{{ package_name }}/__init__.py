"""A double-ended queue of integers, both ends first-class.

make_deque(values) builds one, append/append_left push, pop/pop_left
pull, peek/peek_left read, rotate shifts, to_list answers the
contents. The promise is checked, never assumed: both ends are
first-class, and a rotation never loses an item.
"""

from __future__ import annotations

from .solve import (
    MAX_CAPACITY,
    Deque,
    DequeError,
    append,
    append_left,
    audit_deque,
    make_deque,
    peek,
    peek_left,
    pop,
    pop_left,
    rotate,
    to_list,
)

__version__ = "0.1.0"

__all__ = [
    "MAX_CAPACITY",
    "Deque",
    "DequeError",
    "append",
    "append_left",
    "audit_deque",
    "make_deque",
    "peek",
    "peek_left",
    "pop",
    "pop_left",
    "rotate",
    "to_list",
]
