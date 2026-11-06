from __future__ import annotations

import pytest

from {{ package_name }} import rope as subject

Rope = subject.Rope
RopeError = subject.RopeError

TEXT = "the quick brown fox jumps over the lazy dog"


def rope() -> Rope:
    return Rope(TEXT)


def test_a_fresh_rope_answers_as_the_text_does() -> None:
    found = rope()
    assert found.to_string() == TEXT
    assert len(found) == len(TEXT)
    assert str(found) == TEXT
    assert found.chunks() == [TEXT]


def test_an_empty_rope_holds_nothing_without_lying() -> None:
    empty = Rope("")
    assert empty.to_string() == ""
    assert empty.chunks() == []
    assert len(empty) == 0
    assert empty.is_balanced()


def test_to_string_is_the_join_of_the_chunks_in_order() -> None:
    found = Rope("alpha bravo charlie", max_leaf=5)
    assert found.to_string() == "".join(found.chunks())
    assert all(chunk for chunk in found.chunks())


def test_insert_delete_and_slice_answer_the_shelf() -> None:
    found = rope()
    shelf = TEXT
    found.insert(10, "red ")
    shelf = shelf[:10] + "red " + shelf[10:]
    assert found.to_string() == shelf
    found.append("!!")
    shelf += "!!"
    assert found.to_string() == shelf
    assert found.delete(4, 9) == 5
    shelf = shelf[:4] + shelf[9:]
    assert found.to_string() == shelf
    assert found.slice(4, 8).to_string() == shelf[4:8]
    assert len(found.slice(0, 3)) == 3


def test_negative_offsets_count_from_the_end() -> None:
    found = rope()
    found.insert(-3, "!")
    assert found.to_string() == TEXT[: len(TEXT) - 3] + "!" + TEXT[len(TEXT) - 3 :]


def test_concat_pairs_without_touching_either_side() -> None:
    first = Rope("alpha")
    second = Rope("omega")
    joined = first.concat(second)
    assert joined.to_string() == "alphaomega"
    assert first.to_string() == "alpha"
    assert second.to_string() == "omega"
    assert joined.touches == 0


def test_split_then_concat_rejoins_the_original() -> None:
    found = Rope("0123456789" * 20, max_leaf=7)
    for at in (0, 1, 37, 100, 199, 200):
        left, right = found.split(at)
        assert left.to_string() == ("0123456789" * 20)[:at]
        assert right.to_string() == ("0123456789" * 20)[at:]
        assert left.concat(right).to_string() == found.to_string()


def test_rebalance_moves_shape_and_never_text() -> None:
    found = Rope("seed text", max_leaf=4)
    for _ in range(30):
        found.append(" more")
    before = found.to_string()
    found.rebalance()
    assert found.to_string() == before
    assert found.is_balanced()
    assert found.height() <= found.budget()


def test_edit_cost_tracks_the_spine_not_the_length() -> None:
    small = Rope("a" * 40, max_leaf=4)
    large = Rope("a" * 40_000, max_leaf=64)
    small_touches = small.slice(8, 12).touches
    large_touches = large.slice(20_000, 20_004).touches
    assert large_touches < len(large) // 20
    assert large_touches <= 2 * (large.height() + 2)
    assert large_touches >= small_touches


def test_slices_beyond_the_ends_clamp_instead_of_failing() -> None:
    found = rope()
    assert found.slice(-50, 5).to_string() == TEXT[:5]
    assert found.slice(len(TEXT) - 3, len(TEXT) + 50).to_string() == TEXT[-3:]
    assert found.slice(9, 4).to_string() == ""


def test_a_zero_length_edit_changes_nothing() -> None:
    found = rope()
    assert found.delete(4, 4) == 0
    found.insert(4, "")
    assert found.to_string() == TEXT


def test_shape_reports_every_node_with_its_cached_size() -> None:
    found = rope()
    found.append(" end")
    shape = found.shape()
    assert shape[0].kind == "node"
    assert shape[0].size == len(found)
    kinds = {entry.kind for entry in shape}
    assert kinds == {"node", "leaf"}


def test_a_leaf_of_zero_characters_is_refused() -> None:
    with pytest.raises(RopeError):
        Rope("x", max_leaf=0)


def test_bytes_are_not_text() -> None:
    with pytest.raises(RopeError):
        Rope(b"abc")


def test_concat_needs_a_rope() -> None:
    with pytest.raises(RopeError):
        Rope("x").concat("y")
