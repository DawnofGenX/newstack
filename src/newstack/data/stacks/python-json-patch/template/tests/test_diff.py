from __future__ import annotations

import json
from pathlib import Path

from {{ package_name }} import diff as subject
from {{ package_name }}.patch import apply, equal

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def test_a_diff_applies_to_the_second_document() -> None:
    before = json.loads((FIXTURES / "document.json").read_text())
    after = json.loads((FIXTURES / "after.json").read_text())
    assert equal(apply(before, subject.diff(before, after)), after)


def test_identical_documents_need_no_operations() -> None:
    assert subject.diff({"a": 1}, {"a": 1}) == []


def test_a_number_and_its_float_are_the_same_document() -> None:
    assert subject.diff({"a": 1}, {"a": 1.0}) == []


def test_an_added_key_is_one_add() -> None:
    operations = subject.diff({}, {"a": 1})
    assert operations == [{"op": "add", "path": "/a", "value": 1}]


def test_a_removed_key_is_one_remove() -> None:
    assert subject.diff({"a": 1}, {}) == [{"op": "remove", "path": "/a"}]


def test_a_shorter_list_removes_from_the_end() -> None:
    operations = subject.diff([1, 2, 3], [1])
    assert [operation["path"] for operation in operations] == ["/2", "/1"]


def test_a_longer_list_appends() -> None:
    operations = subject.diff([1], [1, 2, 3])
    assert [operation["op"] for operation in operations] == ["add", "add"]
    assert all(operation["path"] == "/-" for operation in operations)


def test_a_changed_scalar_is_a_replace() -> None:
    assert subject.diff({"a": 1}, {"a": 2}) == [
        {"op": "replace", "path": "/a", "value": 2}]


def test_a_replaced_root_is_one_replace() -> None:
    assert subject.diff(1, 2) == [{"op": "replace", "path": "", "value": 2}]


def test_the_summary_counts_from_one() -> None:
    lines = subject.summary([{"op": "add", "path": "/a", "value": 1}])
    assert lines[0].startswith("  1. add ")
