"""The 64 bits, and the fields that must fit them."""

import pytest

from {{ package_name }} import layout as subject


def test_the_fields_round_trip():
    decoded = subject.decode(subject.compose(1_234, 512, 4095))
    assert (decoded.relative_ms, decoded.worker, decoded.sequence) == (1_234, 512, 4095)


def test_a_larger_millisecond_is_a_larger_identifier():
    assert subject.compose(2, 0, 0) > subject.compose(1, subject.MAX_WORKER, subject.MAX_SEQUENCE)


def test_a_larger_worker_is_a_larger_identifier_within_one_millisecond():
    assert subject.compose(1, 1, 0) > subject.compose(1, 0, subject.MAX_SEQUENCE)


def test_the_capacity_numbers_are_the_bit_counts():
    assert subject.WORKERS == 1 << subject.WORKER_BITS
    assert subject.IDS_PER_MS == 1 << subject.SEQUENCE_BITS
    assert subject.MAX_SEQUENCE == subject.IDS_PER_MS - 1


def test_the_layout_lasts_about_seventy_years():
    assert 69 < subject.years_of_layout() < 70


def test_the_exhaustion_date_is_after_the_epoch():
    assert subject.exhaustion_date() > subject.exhaustion_date(subject.EPOCH_MS - 1_000)


def test_the_capacity_lines_name_every_field():
    text = "\n".join(subject.capacity_lines())
    assert "worker" in text
    assert "sequence" in text
    assert "layout ends" in text


@pytest.mark.parametrize("worker", [-1, subject.MAX_WORKER + 1])
def test_a_worker_outside_the_field_is_refused(worker):
    with pytest.raises(subject.LayoutError, match="worker"):
        subject.compose(1, worker, 0)


@pytest.mark.parametrize("sequence", [-1, subject.MAX_SEQUENCE + 1])
def test_a_sequence_outside_the_field_is_refused(sequence):
    with pytest.raises(subject.LayoutError, match="sequence"):
        subject.compose(1, 0, sequence)


def test_a_negative_timestamp_is_refused():
    with pytest.raises(subject.LayoutError, match="before the epoch"):
        subject.compose(-1, 0, 0)


def test_a_timestamp_past_the_field_is_refused():
    with pytest.raises(subject.LayoutError, match="past the"):
        subject.compose(subject.MAX_RELATIVE_MS + 1, 0, 0)


@pytest.mark.parametrize("value", [True, 1.0, "17"])
def test_a_value_that_is_not_a_whole_number_is_refused(value):
    with pytest.raises(subject.LayoutError):
        subject.compose(value, 0, 0)  # type: ignore[arg-type]


def test_a_negative_identifier_is_refused():
    with pytest.raises(subject.LayoutError, match="negative"):
        subject.decode(-1)


def test_an_identifier_wider_than_sixty_three_bits_is_refused():
    with pytest.raises(subject.LayoutError, match="63 bits"):
        subject.decode(1 << 63)


def test_the_absolute_time_uses_the_epoch():
    decoded = subject.decode(subject.compose(1_000, 0, 0))
    assert decoded.absolute_ms() == subject.EPOCH_MS + 1_000
