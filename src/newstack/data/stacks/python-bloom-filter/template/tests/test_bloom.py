import json

import pytest

from {{ package_name }} import bloom as subject


def filled(count: int = 500) -> subject.Bloom:
    sizing = subject.sized_for(count, 0.01)
    bloom = subject.Bloom(sizing.m_bits, sizing.k_hashes)
    for number in range(count):
        bloom.add(f"present-{number}")
    return bloom


def test_nothing_that_was_added_is_ever_reported_absent() -> None:
    bloom = filled(2_000)
    items = [f"present-{number}" for number in range(2_000)]
    assert [item for item in items if not bloom.might_contain(item)] == []


def test_an_empty_filter_answers_no_to_everything() -> None:
    bloom = subject.Bloom(64, 3)
    assert not bloom.might_contain("anything")
    assert bloom.fill() == 0.0
    assert bloom.predict_rate() == 0.0
    assert bloom.estimate_items() == 0.0


def test_adding_the_same_item_twice_sets_nothing_the_second_time() -> None:
    bloom = subject.Bloom(1_024, 4)
    first = bloom.add("alpha")
    assert len(first) == 4
    assert bloom.add("alpha") == ()
    assert bloom.bits_set() == 4


def test_the_same_items_always_produce_the_same_bits() -> None:
    assert filled(200).as_dict() == filled(200).as_dict()


def test_padding_bits_beyond_the_last_position_are_not_counted() -> None:
    bloom = subject.Bloom(3, 1, b"\xff")
    assert bloom.bits_set() == 3
    assert bloom.fill() == 1.0


def test_the_estimate_inverts_the_formula() -> None:
    bloom = filled(1_000)
    estimate = bloom.estimate_items()
    assert estimate is not None
    assert estimate == pytest.approx(1_000, rel=0.25)


def test_a_full_filter_has_no_invertible_estimate() -> None:
    bloom = subject.Bloom(8, 1, b"\xff")
    assert bloom.estimate_items() is None
    assert bloom.is_saturated()
    assert bloom.predict_rate() == 1.0


def sharing_pair(bloom: subject.Bloom) -> tuple[str, str]:
    """A pair that shares at least one position, so a clear can break the other."""
    for number in range(500):
        keeper, dropped = f"keep-{number}", f"drop-{number}"
        if set(bloom.positions(keeper)) & set(bloom.positions(dropped)):
            return keeper, dropped
    raise AssertionError("no sharing pair in 500 candidates at this size")


def test_clearing_the_bits_of_one_item_can_make_another_disappear() -> None:
    bloom = subject.Bloom(256, 3)
    keeper, dropped = sharing_pair(bloom)
    bloom.add(keeper)
    bloom.add(dropped)
    bloom.clear(dropped)
    assert not bloom.might_contain(keeper), "the guarantee is gone after a clear"


def test_a_position_is_always_inside_the_array() -> None:
    bloom = subject.Bloom(97, 5)
    for position in bloom.positions("anything"):
        assert 0 <= position < 97


def test_a_filter_survives_a_json_round_trip() -> None:
    original = filled(300)
    rebuilt = subject.parse_filter(json.loads(json.dumps(original.as_dict())))
    assert rebuilt.as_dict() == original.as_dict()
    assert rebuilt.might_contain("present-42")


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ([], "a stored filter is a JSON object"),
        ({"type": "sieve"}, "unknown filter type"),
        ({"type": "bloom", "k_hashes": 3, "bits": ""}, "has no m_bits"),
        ({"type": "bloom", "m_bits": 16, "k_hashes": 2}, "has no bit array"),
        ({"type": "bloom", "m_bits": 16, "k_hashes": 2, "bits": "00"}, "holds 1 byte"),
        ({"type": "bloom", "m_bits": 8, "k_hashes": 2, "bits": "zz"}, "not hexadecimal"),
    ],
)
def test_a_stored_filter_that_cannot_be_used_is_refused(payload: object, message: str) -> None:
    with pytest.raises(subject.BloomFilterError, match=message):
        subject.parse_filter(payload)


@pytest.mark.parametrize(("m_bits", "k_hashes"), [(0, 1), (8, 0), (True, 1), (8, 1.5)])
def test_impossible_parameters_are_refused(m_bits: object, k_hashes: object) -> None:
    with pytest.raises(subject.BloomFilterError):
        subject.Bloom(m_bits, k_hashes)  # type: ignore[arg-type]
