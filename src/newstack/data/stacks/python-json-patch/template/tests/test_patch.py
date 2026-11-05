from __future__ import annotations

import copy
import json

import pytest

from {{ package_name }} import patch as subject


def test_add_writes_a_key() -> None:
    assert subject.apply({"a": 1}, [{"op": "add", "path": "/b", "value": 2}]) == {
        "a": 1, "b": 2}


def test_add_inserts_at_an_index() -> None:
    result = subject.apply({"l": ["a", "c"]}, [{"op": "add", "path": "/l/1", "value": "b"}])
    assert result["l"] == ["a", "b", "c"]


def test_add_at_the_end_uses_the_placeholder() -> None:
    result = subject.apply(["a"], [{"op": "add", "path": "/-", "value": "b"}])
    assert result == ["a", "b"]


def test_add_past_the_end_is_refused() -> None:
    with pytest.raises(subject.PatchError, match="past the end"):
        subject.apply(["a"], [{"op": "add", "path": "/3", "value": "x"}])


def test_remove_shifts_the_rest() -> None:
    assert subject.apply(["a", "b"], [{"op": "remove", "path": "/0"}]) == ["b"]


def test_the_root_cannot_be_removed() -> None:
    with pytest.raises(subject.PatchError, match="replace it instead"):
        subject.apply({"a": 1}, [{"op": "remove", "path": ""}])


def test_replace_requires_a_target() -> None:
    with pytest.raises(subject.PatchError, match=r"operation 1 \(replace\) failed"):
        subject.apply({"a": 1}, [{"op": "replace", "path": "/b", "value": 2}])


def test_move_removes_the_source() -> None:
    result = subject.apply({"a": 1}, [{"op": "move", "from": "/a", "path": "/b"}])
    assert result == {"b": 1}


def test_move_into_a_child_is_refused() -> None:
    with pytest.raises(subject.PatchError, match="contain itself"):
        subject.apply({"a": {"b": 1}}, [{"op": "move", "from": "/a", "path": "/a/c"}])


def test_copy_is_deep() -> None:
    document = {"a": {"l": [1]}}
    result = subject.apply(document, [{"op": "copy", "from": "/a", "path": "/b"}])
    result["b"]["l"].append(2)
    assert document["a"]["l"] == [1]


def test_a_failed_test_applies_nothing() -> None:
    document = {"a": 1}
    with pytest.raises(subject.TestFailed, match="test failed"):
        subject.apply(document, [{"op": "add", "path": "/b", "value": 2},
                                {"op": "test", "path": "/a", "value": 9}])
    assert document == {"a": 1}


def test_the_argument_is_never_mutated() -> None:
    document = {"a": [1, 2]}
    before = copy.deepcopy(document)
    subject.apply(document, [{"op": "add", "path": "/a/-", "value": 3}])
    assert document == before


def test_a_single_operation_is_not_a_patch() -> None:
    with pytest.raises(subject.PatchError, match="list of operations"):
        subject.apply({"a": 1}, {"op": "add", "path": "/b", "value": 2})


def test_an_unknown_operation_names_the_known_ones() -> None:
    with pytest.raises(subject.PatchError, match="frobnicate"):
        subject.apply({}, [{"op": "frobnicate", "path": "/a"}])


def test_a_failure_says_nothing_was_applied() -> None:
    with pytest.raises(subject.PatchError, match="nothing was applied"):
        subject.apply({}, [{"op": "remove", "path": "/missing"}])


def test_json_equality_is_numeric() -> None:
    assert subject.equal(1, 1.0)
    assert not subject.equal(True, 1)
    assert not subject.equal("1", 1)


def test_a_patch_file_must_be_a_list(tmp_path) -> None:
    path = tmp_path / "patch.json"
    path.write_text(json.dumps({"op": "add", "path": "/a", "value": 1}))
    with pytest.raises(subject.PatchError, match="list of operations"):
        subject.load(path)
