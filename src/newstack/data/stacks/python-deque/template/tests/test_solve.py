from __future__ import annotations

from {{ package_name }}.solve import (
    MAX_CAPACITY,
    DequeError,
    append,
    append_left,
    make_deque,
    pop,
    pop_left,
    rotate,
    to_list,
)


def test_empty() -> None:
    assert to_list(make_deque(())) == []


def test_append_pop() -> None:
    d = make_deque((1, 2))
    append(d, 3)
    assert to_list(d) == [1, 2, 3]
    assert pop(d) == 3
    assert to_list(d) == [1, 2]


def test_appendleft_popleft() -> None:
    d = make_deque((1, 2))
    append_left(d, 0)
    assert to_list(d) == [0, 1, 2]
    assert pop_left(d) == 0
    assert to_list(d) == [1, 2]


def test_rotate_keeps_items() -> None:
    d = make_deque((1, 2, 3))
    rotate(d, 1)
    assert sorted(to_list(d)) == [1, 2, 3]


def test_oversized_refused() -> None:
    import pytest

    with pytest.raises(DequeError):
        make_deque(list(range(MAX_CAPACITY + 1)))


def test_non_int_refused() -> None:
    import pytest

    with pytest.raises(DequeError):
        make_deque((1, "a"))


def test_pop_empty_refused() -> None:
    import pytest

    with pytest.raises(DequeError):
        pop(make_deque(()))
