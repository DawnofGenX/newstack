import json
from pathlib import Path

import pytest

from {{ package_name }} import events as subject


def test_an_offset_timestamp_is_microseconds() -> None:
    assert subject.to_us("2026-01-01T00:00:00+00:00") == 1_767_225_600_000_000


def test_a_naive_timestamp_is_refused() -> None:
    with pytest.raises(subject.EventError) as caught:
        subject.to_us("2026-01-01T00:00:00")
    assert "local guess" in str(caught.value)


def test_a_boolean_is_not_a_timestamp() -> None:
    with pytest.raises(subject.EventError):
        subject.Event(True)


def test_a_boolean_is_not_a_value() -> None:
    with pytest.raises(subject.EventError):
        subject.Event(0, True)


def test_load_keeps_arrival_order(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    path.write_text(
        "\n".join(
            [
                json.dumps({"t": "2026-01-01T00:00:10+00:00", "value": 1}),
                json.dumps({"t": "2026-01-01T00:00:05+00:00", "value": 2}),
            ]
        )
        + "\n"
    )
    loaded = subject.load(path)
    assert [event.value for event in loaded] == [1, 2]
    assert loaded[0].t_us > loaded[1].t_us


def test_a_torn_last_line_is_refused_by_the_loader(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    path.write_text('{"t": "2026-01-01T00:00:00+00:00", "value": 1}\n{"t": "2026')
    with pytest.raises(subject.EventError):
        subject.load(path)


def test_an_open_ended_record_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    path.write_text(json.dumps({"value": 1}) + "\n")
    with pytest.raises(subject.EventError):
        subject.load(path)
