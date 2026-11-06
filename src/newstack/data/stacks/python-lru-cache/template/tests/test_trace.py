"""A published hit ratio is only reproducible if the trace is."""

import pytest

from {{ package_name }} import trace as subject


@pytest.mark.parametrize("name", subject.TRACES)
def test_the_same_seed_builds_the_same_trace(name):
    assert subject.build(name, 300, seed=7) == subject.build(name, 300, seed=7)


@pytest.mark.parametrize("name", subject.TRACES)
def test_the_trace_has_the_length_asked_for(name):
    assert len(subject.build(name, 500)) == 500


@pytest.mark.parametrize("name", subject.TRACES)
def test_every_access_is_a_key(name):
    assert all(isinstance(key, str) and key for key in subject.build(name, 200))


@pytest.mark.parametrize("name", subject.TRACES)
def test_every_trace_has_a_description(name):
    assert subject.describe(name)


def test_a_different_seed_builds_a_different_zipf_trace():
    assert subject.zipf_trace(400, seed=7) != subject.zipf_trace(400, seed=8)


def test_zipf_is_skewed():
    counts = subject.frequency(subject.zipf_trace(4000))
    hottest = counts.most_common(1)[0][1]
    assert hottest > 40
    assert counts.most_common(1)[0][1] > counts.most_common()[-1][1] * 3


def test_a_larger_skew_concentrates_the_traffic():
    flat = subject.frequency(subject.zipf_trace(4000, skew=0.5)).most_common(1)[0][1]
    sharp = subject.frequency(subject.zipf_trace(4000, skew=1.5)).most_common(1)[0][1]
    assert sharp > flat


def test_the_loop_repeats_one_fixed_order():
    loop = subject.loop_trace(300, 100)
    assert loop[:100] == loop[100:200]


def test_the_loop_uses_every_key():
    assert len(set(subject.loop_trace(400, 100))) == 100


def test_the_scan_visits_keys_it_will_never_reuse():
    scan = subject.scan_trace(400, hot=10)
    cold = [key for key in scan if key.startswith("scan-")]
    assert len(cold) > 100
    assert len(set(cold)) == len(cold)


def test_the_hot_share_needs_to_be_a_fraction():
    with pytest.raises(subject.TraceError, match=r"0\.\.1"):
        subject.scan_trace(100, hot=5, hot_share=1.5)


def test_the_mixed_trace_keeps_two_namespaces_apart():
    mixed = subject.mixed_trace(400)
    assert any(key.startswith("loop-") for key in mixed)
    assert any(not key.startswith("loop-") for key in mixed)


def test_an_unknown_trace_is_refused():
    with pytest.raises(subject.TraceError, match="known traces are"):
        subject.build("spiral", 10)


@pytest.mark.parametrize("length,keys", [(0, 10), (10, 0)])
def test_a_trace_needs_at_least_one_access_and_one_key(length, keys):
    with pytest.raises(subject.TraceError):
        subject.zipf_trace(length, keys)


def test_a_non_positive_skew_is_refused():
    with pytest.raises(subject.TraceError, match="skew"):
        subject.zipf_trace(10, skew=0)
