import json

import pytest

from {{ package_name }} import dataset
from {{ package_name }}.dataset import DatasetError


def write(tmp_path, rows, name="rows.jsonl"):
    path = tmp_path / name
    lines = [row if isinstance(row, str) else json.dumps(row) for row in rows]
    path.write_text("\n".join(lines) + "\n")
    return path


def test_examples_keep_file_order_and_blank_lines_are_skipped(tmp_path):
    rows = [{"id": "a", "prompt": "q", "gold": "x"}, "", {"id": "b", "prompt": "q", "gold": "y"}]
    path = write(tmp_path, rows)
    assert [example.id for example in dataset.load_examples(path)] == ["a", "b"]


def test_a_malformed_line_names_the_file_and_line(tmp_path):
    path = write(tmp_path, [{"id": "a", "prompt": "q", "gold": "x"}, "{not json"])
    with pytest.raises(DatasetError, match=r"rows\.jsonl:2: not JSON"):
        dataset.load_examples(path)


def test_a_missing_member_names_the_file_and_line(tmp_path):
    path = write(tmp_path, [{"id": "a", "prompt": "q"}])
    with pytest.raises(DatasetError, match=r"rows\.jsonl:1: missing 'gold'"):
        dataset.load_examples(path)


def test_a_non_string_member_is_rejected(tmp_path):
    path = write(tmp_path, [{"id": "a", "prompt": "q", "gold": 4}])
    with pytest.raises(DatasetError, match="'gold' must be a string"):
        dataset.load_examples(path)


def test_duplicate_ids_are_rejected(tmp_path):
    rows = [{"id": "a", "prompt": "q", "gold": "x"}, {"id": "a", "prompt": "q", "gold": "y"}]
    path = write(tmp_path, rows)
    with pytest.raises(DatasetError, match="duplicate id 'a'"):
        dataset.load_examples(path)


def test_an_empty_file_is_not_a_dataset(tmp_path):
    path = write(tmp_path, [])
    with pytest.raises(DatasetError, match="no examples"):
        dataset.load_examples(path)


def test_a_missing_file_says_so(tmp_path):
    with pytest.raises(DatasetError, match="cannot read"):
        dataset.load_examples(tmp_path / "nope.jsonl")


def test_predictions_parse_from_any_iterable_of_lines():
    rows = [
        '{"id": "a", "prediction": "Paris"}',
        '{"id": "b", "prediction": "Tokyo"}',
    ]
    assert dataset.parse_predictions(rows) == {"a": "Paris", "b": "Tokyo"}
