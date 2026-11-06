"""Every policy forgets something; these tests say exactly what."""

import pytest

from {{ package_name }} import cache as subject


@pytest.mark.parametrize("name", sorted(subject.POLICIES))
def test_a_policy_misses_on_the_way_in_and_hits_on_the_way_back(name):
    policy = subject.by_name(name)(3)
    assert [policy.access(key) for key in ("a", "b", "c")] == [False, False, False]
    assert policy.access("b") is True
    assert policy.evictions == 0


@pytest.mark.parametrize("name", sorted(subject.POLICIES))
def test_a_fourth_distinct_key_evicts_exactly_one(name):
    policy = subject.by_name(name)(3)
    for key in ("a", "b", "c", "d"):
        policy.access(key)
    assert policy.evictions == 1
    assert len(policy) == 3


def test_fifo_forgets_the_oldest_arrival_even_when_it_was_reused():
    policy = subject.by_name("fifo")(2)
    for key in ("a", "b", "a", "c"):
        policy.access(key)
    assert policy.resident() == {"b", "c"}


def test_lru_keeps_the_key_that_was_just_used():
    policy = subject.by_name("lru")(2)
    for key in ("a", "b", "a", "c"):
        policy.access(key)
    assert policy.resident() == {"a", "c"}


def test_clock_spends_scans_instead_of_reordering():
    policy = subject.by_name("clock")(2)
    for key in ("a", "b", "a", "c"):
        policy.access(key)
    assert policy.scans >= 2
    assert len(policy) == policy.capacity


def test_clock_clears_a_bit_before_it_takes_the_slot():
    policy = subject.by_name("clock")(2)
    policy.access("a")
    policy.access("b")
    policy.access("c")
    assert "a" not in policy.resident()
    assert policy.resident() == {"b", "c"}


def test_slru_promotes_a_repeat_off_probation():
    policy = subject.by_name("slru")(10, 0.8)
    policy.access("hot")
    policy.access("hot")
    assert policy.promotions == 1
    assert "hot" in policy.resident()


def test_slru_keeps_the_promoted_key_through_a_scan():
    policy = subject.by_name("slru")(10, 0.8)
    for _ in range(2):
        policy.access("hot")
    for number in range(20):
        policy.access(f"scan-{number}")
    assert "hot" in policy.resident()
    assert len(policy) == 10


def test_slru_needs_a_share_between_zero_and_one():
    with pytest.raises(subject.CacheError, match="fraction"):
        subject.by_name("slru")(4, 1.5)


@pytest.mark.parametrize("capacity", [0, -1])
def test_a_capacity_below_one_is_refused(capacity):
    with pytest.raises(subject.CacheError, match="at least one key"):
        subject.by_name("lru")(capacity)


def test_a_bool_capacity_is_refused():
    with pytest.raises(subject.CacheError, match="whole number"):
        subject.by_name("lru")(True)


def test_a_non_string_key_is_refused():
    with pytest.raises(subject.CacheError, match="string"):
        subject.by_name("lru")(2).access(7)


def test_an_unknown_policy_name_lists_the_known_ones():
    with pytest.raises(subject.CacheError, match="known policies are"):
        subject.by_name("mru")


def test_the_hit_rate_counts_every_access():
    policy = subject.by_name("lru")(2)
    for key in ("a", "a", "b", "c"):
        policy.access(key)
    assert policy.accesses == 4
    assert policy.hits == 1
    assert policy.hit_rate == pytest.approx(0.25)
