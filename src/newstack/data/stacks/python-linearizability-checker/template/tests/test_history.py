import json

import pytest

from {{ package_name }} import history as subject


def line(client, kind, value, start, end):
    return json.dumps({"client": client, "op": kind, "value": value, "start": start, "end": end})


def test_a_header_sets_the_initial_value():
    parsed = subject.parse_lines(['{"initial": 4}', line(0, "read", 4, 0, 1)])
    assert parsed.initial == 4
    assert len(parsed) == 1


def test_a_second_header_is_refused():
    with pytest.raises(subject.HistoryError, match="second header"):
        subject.parse_lines(['{"initial": 4}', '{"initial": 5}'])


def test_a_header_with_extras_is_refused():
    with pytest.raises(subject.HistoryError, match="only 'initial'"):
        subject.parse_lines(['{"initial": 4, "client": 0}'])


def test_comments_and_blank_lines_are_skipped():
    parsed = subject.parse_lines(["", "# a note", line(0, "write", 1, 0, 1)])
    assert len(parsed) == 1


def test_a_malformed_line_names_its_number():
    with pytest.raises(subject.HistoryError, match="line 2 is not JSON"):
        subject.parse_lines([line(0, "write", 1, 0, 1), "{"])


def test_a_non_object_line_is_refused():
    with pytest.raises(subject.HistoryError, match="JSON object"):
        subject.parse_lines(["[1, 2]"])


def test_an_unknown_key_is_refused_with_the_key_named():
    payload = json.dumps({"client": 0, "op": "read", "value": 1, "start": 0, "end": 1, "x": 1})
    with pytest.raises(subject.HistoryError, match="unknown key 'x'"):
        subject.parse_lines([payload])


def test_a_missing_key_is_refused_with_the_key_named():
    payload = json.dumps({"client": 0, "op": "read", "value": 1, "start": 0})
    with pytest.raises(subject.HistoryError, match="missing 'end'"):
        subject.parse_lines([payload])


def test_a_boolean_is_not_a_whole_number():
    payload = json.dumps({"client": 0, "op": "read", "value": 1, "start": False, "end": 1})
    with pytest.raises(subject.HistoryError, match="whole number"):
        subject.parse_lines([payload])


def test_a_negative_client_is_refused():
    with pytest.raises(subject.HistoryError, match="cannot be negative"):
        subject.parse_lines([line(-1, "read", 1, 0, 1)])


def test_a_response_before_its_invocation_is_refused():
    with pytest.raises(subject.HistoryError, match="comes before the invocation"):
        subject.parse_lines([line(0, "read", 1, 5, 1)])


def test_a_negative_time_is_refused():
    with pytest.raises(subject.HistoryError, match="cannot be negative"):
        subject.parse_lines([line(0, "read", 1, -1, 1)])


def test_an_unknown_kind_is_refused():
    with pytest.raises(subject.HistoryError, match="'op' must be one of"):
        subject.parse_lines([line(0, "scan", 1, 0, 1)])


def test_overlapping_operations_of_one_client_are_refused():
    lines = [line(0, "write", 1, 0, 5), line(0, "read", 1, 4, 6)]
    with pytest.raises(subject.HistoryError, match="overlap in time"):
        subject.parse_lines(lines)


def test_touching_operations_of_one_client_are_allowed():
    parsed = subject.parse_lines([line(0, "write", 1, 0, 5), line(0, "read", 1, 5, 6)])
    assert len(parsed) == 2


def test_precedence_needs_a_strict_gap():
    first = subject.Operation(0, "write", 1, 0, 2)
    second = subject.Operation(1, "read", 1, 2, 3)
    assert first.precedes(second) is False
    assert first.overlaps(second) is True


def test_restricting_keeps_order_and_the_initial_value():
    history = subject.History(
        (
            subject.Operation(0, "write", 1, 0, 1),
            subject.Operation(0, "read", 1, 2, 3),
        ),
        initial=7,
    )
    kept = history.restricted([1])
    assert [op.kind for op in kept.operations] == ["read"]
    assert kept.initial == 7


def test_the_span_covers_every_operation():
    history = subject.History(
        (subject.Operation(0, "write", 1, 2, 4), subject.Operation(1, "read", 1, 6, 9))
    )
    assert history.span == 7


def test_a_missing_file_is_named(tmp_path):
    with pytest.raises(subject.HistoryError, match="no such history"):
        subject.load(tmp_path / "missing.jsonl")


def test_clients_are_sorted_and_unique():
    history = subject.History(
        (
            subject.Operation(2, "write", 1, 0, 1),
            subject.Operation(0, "read", 1, 2, 3),
            subject.Operation(2, "read", 1, 4, 5),
        )
    )
    assert history.clients == (0, 2)
    assert len(history.of_client(2)) == 2
