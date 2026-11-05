"""One event: what the hash covers and what it refuses to cover."""

from __future__ import annotations

import pytest

from {{ package_name }} import record as subject


def test_the_first_event_links_to_genesis() -> None:
    body = subject.body_of(1, "alice", "note.update", "note/1")
    assert body["prev_hash"] == subject.GENESIS
    assert len(subject.GENESIS) == 64


def test_the_hash_covers_the_body_but_is_not_part_of_it() -> None:
    body = subject.body_of(1, "alice", "note.update", "note/1", detail={"field": "title"})
    event = subject.event_of(body)
    assert "hash" not in event.body
    assert event.hash == subject.hash_of(event.body)


def test_the_hash_changes_when_any_field_changes() -> None:
    base = subject.body_of(1, "alice", "note.update", "note/1")
    other = subject.body_of(1, "alice", "note.update", "note/2")
    assert subject.hash_of(base) != subject.hash_of(other)


def test_the_timestamp_defaults_to_utc_with_an_offset() -> None:
    body = subject.body_of(1, "alice", "note.update", "note/1")
    assert body["at"].endswith("+00:00") or body["at"].endswith("Z")


@pytest.mark.parametrize(
    "at",
    ["2026-11-05T10:00:00", "2026-11-05 10:00:00+00:00", "yesterday", "2026-11-05T10:00:00+05:30"],
)
def test_a_non_utc_timestamp_is_refused(at: str) -> None:
    with pytest.raises(ValueError, match="ISO-8601 UTC"):
        subject.body_of(1, "alice", "note.update", "note/1", at=at)


@pytest.mark.parametrize(
    ("kwargs", "pattern"),
    [
        ({"actor": ""}, "actor must be a non-empty string"),
        ({"action": "  "}, "action must be a non-empty string"),
        ({"target": ""}, "target must be a non-empty string"),
        ({"seq": 0}, "seq must be a positive integer"),
        ({"seq": True}, "seq must be a positive integer"),
        ({"detail": {"ratio": 0.5}}, "is a float"),
        ({"detail": ["not", "a", "mapping"]}, "detail must be a mapping"),
        ({"prev_hash": "abc"}, "prev_hash must be 64 lowercase hex"),
    ],
)
def test_unusable_input_is_refused(kwargs: dict, pattern: str) -> None:
    arguments = {"seq": 1, "actor": "alice", "action": "a", "target": "t", **kwargs}
    with pytest.raises(ValueError, match=pattern):
        subject.body_of(
            arguments.pop("seq"),
            arguments.pop("actor"),
            arguments.pop("action"),
            arguments.pop("target"),
            **arguments,
        )


def test_an_event_survives_the_stored_round_trip() -> None:
    body = subject.body_of(2, "alice", "note.update", "note/1", detail={"field": "title"})
    stored = subject.event_of(body)
    again = subject.stored_event(subject.canonical(body), stored.hash)
    assert again.body == stored.body
    assert again.hash == stored.hash


def test_a_stored_body_that_is_not_json_is_refused() -> None:
    with pytest.raises(ValueError, match="not JSON"):
        subject.stored_event("{nope", "0" * 64)


def test_a_stored_body_missing_fields_is_refused() -> None:
    with pytest.raises(ValueError, match="stored body is missing") as caught:
        subject.stored_event('{"seq":1}', "0" * 64)
    assert "actor" in str(caught.value)
