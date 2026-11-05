import json

import pytest

from {{ package_name }} import buckets as subject

START = 1_772_000_000 - (1_772_000_000 % 60)


def write(tmp_path, rows, name="traffic.jsonl"):
    path = tmp_path / name
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    return path


def test_reading_a_stream_of_buckets(tmp_path):
    path = write(
        tmp_path,
        [
            {"at": START, "good": 100, "bad": 1},
            {"at": START + 60, "good": 100, "bad": 0},
        ],
    )
    loaded = subject.load(path)
    assert [bucket.at_s for bucket in loaded] == [START, START + 60]
    assert loaded[0].total == 101


def test_iso_timestamps_are_accepted(tmp_path):
    path = write(tmp_path, [{"at": "2026-03-08T00:00:00Z", "good": 1, "bad": 0}])
    assert subject.load(path)[0].at_s == 1772928000


def test_buckets_are_sorted_even_when_the_file_is_not(tmp_path):
    path = write(
        tmp_path,
        [
            {"at": START + 60, "good": 1, "bad": 0},
            {"at": START, "good": 1, "bad": 0},
        ],
    )
    assert [bucket.at_s for bucket in subject.load(path)] == [START, START + 60]


@pytest.mark.parametrize(
    ("row", "fragment"),
    [
        ({"at": START + 30, "good": 1, "bad": 0}, "not aligned"),
        ({"at": START, "good": -1, "bad": 0}, "cannot be negative"),
        ({"at": START, "good": True, "bad": 0}, "must be an integer"),
        ({"at": START, "good": 1}, "missing 'bad'"),
        ({"at": START, "good": 1, "bad": 0, "ugly": 1}, "unknown field"),
        ({"at": "2026-03-08T00:00:00", "good": 1, "bad": 0}, "has no offset"),
        ({"at": "not a time", "good": 1, "bad": 0}, "is not ISO 8601"),
    ],
)
def test_a_bucket_that_cannot_be_trusted(tmp_path, row, fragment):
    path = write(tmp_path, [row])
    with pytest.raises(subject.ReadingError, match=fragment):
        subject.load(path)


def test_a_repeated_bucket_would_count_traffic_twice(tmp_path):
    path = write(
        tmp_path,
        [
            {"at": START, "good": 1, "bad": 0},
            {"at": START, "good": 1, "bad": 0},
        ],
    )
    with pytest.raises(subject.ReadingError, match="count the same traffic twice"):
        subject.load(path)


def test_lines_that_are_not_json(tmp_path):
    path = tmp_path / "bad.jsonl"
    path.write_text("{not json}\n", encoding="utf-8")
    with pytest.raises(subject.ReadingError, match="not JSON"):
        subject.load(path)


def test_an_empty_file_is_an_error(tmp_path):
    path = tmp_path / "empty.jsonl"
    path.write_text("\n", encoding="utf-8")
    with pytest.raises(subject.ReadingError, match="no buckets"):
        subject.load(path)


def test_a_missing_file_is_an_error(tmp_path):
    with pytest.raises(subject.ReadingError, match="cannot read"):
        subject.load(tmp_path / "nope.jsonl")


def test_gaps_are_stretches_with_no_bucket(tmp_path):
    path = write(
        tmp_path,
        [
            {"at": START, "good": 1, "bad": 0},
            {"at": START + 60, "good": 1, "bad": 0},
            {"at": START + 240, "good": 1, "bad": 0},
        ],
    )
    loaded = subject.load(path)
    assert subject.gaps(loaded) == [(START + 120, START + 240)]


def test_between_selects_whole_buckets_only():
    reads = [subject.Bucket(START + 60 * index, 1, 0) for index in range(5)]
    assert len(subject.between(reads, START, START + 180)) == 3
    assert subject.totals(reads) == (5, 0)
