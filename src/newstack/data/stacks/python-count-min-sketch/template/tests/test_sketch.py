import pytest

from {{ package_name }} import sketch as subject


def test_a_hash_is_stable_across_calls() -> None:
    assert subject.row_hashes("alpha", 4) == subject.row_hashes("alpha", 4)


def test_rows_are_independent_enough_to_differ() -> None:
    assert len(set(subject.row_hashes("alpha", 4))) == 4


def test_two_items_do_not_share_every_row_hash() -> None:
    assert subject.row_hashes("alpha", 1) != subject.row_hashes("beta", 1)


def test_depth_is_bounded_by_one_digest() -> None:
    with pytest.raises(subject.SketchError, match="at most 8"):
        subject.row_hashes("x", 9)


@pytest.mark.parametrize("depth", [0, -1])
def test_a_depth_below_one_is_refused(depth: int) -> None:
    with pytest.raises(subject.SketchError, match="at least 1"):
        subject.row_hashes("x", depth)


def test_the_error_bound_is_a_function_of_width_only() -> None:
    assert subject.epsilon(512) == pytest.approx(2.718281828 / 512, rel=1e-6)


def test_delta_falls_with_depth() -> None:
    assert subject.delta(2) > subject.delta(5)


def test_an_unseen_item_estimates_zero() -> None:
    assert subject.CountMinSketch(64, 4).estimate("nothing") == 0


def test_an_item_counts_its_own_updates() -> None:
    sketch = subject.CountMinSketch(64, 4)
    sketch.add("a", 3)
    assert sketch.estimate("a") == 3
    assert (sketch.total, sketch.updates) == (3, 1)


def test_collisions_never_lower_an_estimate() -> None:
    sketch = subject.CountMinSketch(4, 3)
    for item in ("a", "b", "c", "d", "e"):
        sketch.add(item)
    assert sketch.estimate("e") >= 1


@pytest.mark.parametrize("count", [0, -1, True])
def test_a_count_must_be_a_positive_whole_number(count: object) -> None:
    with pytest.raises(subject.SketchError):
        subject.CountMinSketch(64, 4).add("a", count)  # type: ignore[arg-type]


def test_a_conservative_update_only_touches_the_minimum() -> None:
    """A narrow sketch forces collisions, which is where the two styles differ."""
    plain = subject.CountMinSketch(4, 4)
    careful = subject.CountMinSketch(4, 4, conservative=True)
    for item in ("a", "b", "c", "d", "e", "f"):
        plain.add(item)
        careful.add(item)
    assert sum(sum(row) for row in careful.rows) < sum(sum(row) for row in plain.rows)


def test_merge_adds_the_rows() -> None:
    left = subject.CountMinSketch(64, 3)
    right = subject.CountMinSketch(64, 3)
    left.add("a", 3)
    right.add("a", 2)
    merged = left.merge(right)
    assert merged.estimate("a") == 5
    assert merged.total == 5


def test_merge_refuses_a_different_shape() -> None:
    with pytest.raises(subject.SketchError, match="would not line up"):
        subject.CountMinSketch(64, 3).merge(subject.CountMinSketch(128, 3))


def test_merge_refuses_mixed_update_styles() -> None:
    with pytest.raises(subject.SketchError, match="would not describe either half"):
        subject.CountMinSketch(64, 3).merge(subject.CountMinSketch(64, 3, conservative=True))


def test_a_sketch_round_trips() -> None:
    sketch = subject.CountMinSketch(64, 3)
    sketch.add("a", 2)
    assert subject.parse_sketch(sketch.as_dict()).as_dict() == sketch.as_dict()


def test_another_type_is_refused() -> None:
    with pytest.raises(subject.SketchError, match="not a count-min sketch"):
        subject.parse_sketch({"type": "bloom"})


def test_a_row_of_the_wrong_length_is_refused() -> None:
    payload = subject.CountMinSketch(64, 2).as_dict()
    payload["rows"] = [[0] * 64]
    with pytest.raises(subject.SketchError, match="needs that many rows"):
        subject.parse_sketch(payload)


def test_a_negative_counter_is_refused() -> None:
    payload = subject.CountMinSketch(64, 2).as_dict()
    payload["rows"][0][0] = -1
    with pytest.raises(subject.SketchError, match="not a counter"):
        subject.parse_sketch(payload)
