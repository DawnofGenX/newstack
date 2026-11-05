from {{ package_name }} import measure as subject


def test_the_stream_is_skewed_and_deterministic() -> None:
    counts = subject.skewed_counts(20, 1_000)
    assert counts == subject.skewed_counts(20, 1_000)
    assert counts["user:0001"] > counts["user:0020"]


def test_every_item_arrives_at_least_once() -> None:
    counts = subject.skewed_counts(300, 100)
    assert min(counts.values()) >= 1
    assert len(counts) == 300


def test_the_report_counts_no_underestimates() -> None:
    counts = subject.skewed_counts(60, 3_000)
    found = subject.report(subject.filled(counts, 256, 4), counts)
    assert found.underestimates == 0
    assert found.total == sum(counts.values())


def test_the_promise_scales_with_the_updates() -> None:
    counts = subject.skewed_counts(30, 1_000)
    sketch = subject.filled(counts, 256, 4)
    assert sketch.bound() == subject.report(sketch, counts).bound


def test_a_wider_sketch_is_not_worse() -> None:
    counts = subject.skewed_counts(80, 4_000)
    narrow = subject.report(subject.filled(counts, 128, 4), counts)
    wide = subject.report(subject.filled(counts, 512, 4), counts)
    assert wide.mean_over <= narrow.mean_over


def test_the_top_items_keep_their_order() -> None:
    counts = subject.skewed_counts(50, 5_000)
    shown = subject.top(subject.filled(counts, 512, 4), counts, 3)
    assert [item for item, _, _ in shown] == ["user:0001", "user:0002", "user:0003"]


def test_an_empty_comparison_is_refused() -> None:
    sketch = subject.filled({"a": 1}, 64, 3)
    try:
        subject.report(sketch, {})
    except ValueError as error:
        assert "nothing to compare" in str(error)
    else:
        raise AssertionError("an empty truth was accepted")
