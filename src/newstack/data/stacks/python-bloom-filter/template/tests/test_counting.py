import json

import pytest

from {{ package_name }} import bloom as subject


def test_removing_what_was_added_restores_the_filter() -> None:
    bloom = subject.CountingBloom(4_096, 3)
    bloom.add("alpha")
    bloom.add("beta")
    before = bloom.bits_set()
    bloom.remove("alpha")
    assert bloom.might_contain("alpha") is False
    assert bloom.might_contain("beta") is True
    assert bloom.bits_set() <= before - 1


def sharing_pair(bloom: subject.CountingBloom) -> tuple[str, str]:
    for number in range(500):
        keeper, dropped = f"keep-{number}", f"drop-{number}"
        if set(bloom.positions(keeper)) & set(bloom.positions(dropped)):
            return keeper, dropped
    raise AssertionError("no sharing pair in 500 candidates at this size")


def test_a_shared_position_survives_a_removal_that_a_plain_clear_would_destroy() -> None:
    naive = subject.Bloom(256, 3)
    counting = subject.CountingBloom(256, 3)
    keeper, dropped = sharing_pair(counting)
    for bloom in (naive, counting):
        bloom.add(keeper)
        bloom.add(dropped)
    naive.clear(dropped)
    counting.remove(dropped)
    assert not naive.might_contain(keeper), "clearing erased a bit the keeper needed"
    assert counting.might_contain(keeper), "the counter only dropped by one"
    assert not counting.might_contain(dropped)


def test_removing_something_never_added_is_refused() -> None:
    bloom = subject.CountingBloom(256, 2)
    with pytest.raises(subject.BloomFilterError, match="no record of the add"):
        bloom.remove("ghost")


def test_counters_stop_at_the_ceiling_and_say_so() -> None:
    bloom = subject.CountingBloom(8, 1)
    for _ in range(subject.SATURATION + 5):
        bloom.add("same")
    assert bloom.saturated_positions() == 1
    assert bloom.as_dict()["counters"].startswith(f"{subject.SATURATION:02x}")


def test_a_counting_filter_reports_its_own_fill() -> None:
    bloom = subject.CountingBloom(1_024, 4)
    assert bloom.fill() == 0.0
    bloom.add("alpha")
    assert 0 < bloom.fill() < 1
    assert bloom.is_saturated() is False


def test_a_counting_filter_survives_a_json_round_trip() -> None:
    bloom = subject.CountingBloom(512, 3)
    bloom.add("alpha")
    rebuilt = subject.parse_filter(json.loads(json.dumps(bloom.as_dict())))
    assert isinstance(rebuilt, subject.CountingBloom)
    assert rebuilt.as_dict() == bloom.as_dict()
    rebuilt.remove("alpha")
    assert not rebuilt.might_contain("alpha")


def test_a_counter_array_of_the_wrong_length_is_refused() -> None:
    payload = {"type": "counting-bloom", "m_bits": 8, "k_hashes": 1, "counters": "0000"}
    with pytest.raises(subject.BloomFilterError, match="holds 2 counter"):
        subject.parse_filter(payload)


def test_counting_filters_have_no_invertible_estimate_when_full() -> None:
    bloom = subject.CountingBloom(2, 1)
    bloom.add("alpha")
    bloom.add("alpha")
    assert bloom.estimate_items() is not None
