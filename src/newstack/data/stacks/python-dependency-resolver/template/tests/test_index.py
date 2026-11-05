import json

import pytest

from {{ package_name }} import index as subject


def build(packages):
    return subject.parse_index({"packages": packages})


def test_candidates_come_back_highest_first():
    index = build({"shared": {"1.0.0": {}, "1.4.0": {}, "2.0.0": {}}})
    from {{ package_name }} import ranges

    picked = index.candidates("shared", ranges.parse_range("^1.0.0"))
    assert [version.text for version in picked] == ["1.4.0", "1.0.0"]


def test_a_missing_dependency_is_an_authoring_error_not_a_conflict():
    with pytest.raises(subject.IndexError_) as caught:
        build({"web": {"1.0.0": {"shared": "^1.0.0"}}})
    assert "web 1.0.0 depends on 'shared'" in str(caught.value)


def test_two_spellings_of_one_version_are_refused():
    with pytest.raises(subject.IndexError_) as caught:
        build({"shared": {"1.0.0": {}, "1.0.0+build.1": {}}})
    assert "two spellings" in str(caught.value)


def test_a_package_with_no_versions_is_refused():
    with pytest.raises(subject.IndexError_) as caught:
        build({"shared": {}})
    assert "publishes no versions" in str(caught.value)


def test_a_bad_range_names_the_release_that_carries_it():
    with pytest.raises(subject.IndexError_) as caught:
        build({"web": {"1.0.0": {"shared": "banana"}}, "shared": {"1.0.0": {}}})
    assert "web 1.0.0" in str(caught.value)


def test_load_wraps_the_filename(tmp_path):
    path = tmp_path / "index.json"
    path.write_text(json.dumps({"packages": {"shared": {}}}))
    with pytest.raises(subject.IndexError_) as caught:
        subject.load(path)
    assert str(path) in str(caught.value)


def test_load_says_so_when_the_file_is_absent(tmp_path):
    with pytest.raises(subject.IndexError_) as caught:
        subject.load(tmp_path / "absent.json")
    assert "no index at" in str(caught.value)


def test_the_fixture_index_is_valid():
    index = subject.load("fixtures/index.json")
    assert "shared" in index.names()
    assert index.published("shared")[-1] == "3.0.0-rc.1"
