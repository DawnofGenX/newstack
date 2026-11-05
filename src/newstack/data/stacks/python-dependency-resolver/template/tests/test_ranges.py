from {{ package_name }} import ranges as subject
from {{ package_name }} import versions as v


def allows(text, candidate):
    return subject.parse_range(text).allows(v.parse(candidate))


def test_caret_allows_the_whole_major_above_one():
    assert allows("^1.2.3", "1.2.3")
    assert allows("^1.2.3", "1.9.9")
    assert not allows("^1.2.3", "2.0.0")
    assert not allows("^1.2.3", "1.2.2")


def test_caret_at_zero_freezes_the_leftmost_non_zero_part():
    assert allows("^0.2.3", "0.2.9")
    assert not allows("^0.2.3", "0.3.0")
    assert allows("^0.0.3", "0.0.3")
    assert not allows("^0.0.3", "0.0.4")


def test_a_bare_caret_zero_means_anything_before_one():
    assert allows("^0", "0.9.9")
    assert not allows("^0", "1.0.0")


def test_tilde_freezes_everything_above_the_last_component_written():
    assert allows("~1.2.3", "1.2.9")
    assert not allows("~1.2.3", "1.3.0")
    assert allows("~1.2", "1.2.7")
    assert not allows("~1.2", "1.3.0")
    assert allows("~1", "1.9.9")
    assert not allows("~1", "2.0.0")


def test_prereleases_are_opt_in():
    assert not allows(">=1.0.0", "1.1.0-rc.1")
    assert not allows("^2.0.0", "3.0.0-rc.1")
    assert not allows("*", "1.0.0-rc.1")
    assert allows(">=3.0.0-rc.1", "3.0.0-rc.1")
    assert allows("^3.0.0-rc.1", "3.0.0-rc.2")


def test_comparator_sets_and_unions():
    assert allows(">=1.0.0 <2.0.0", "1.4.0")
    assert not allows(">=1.0.0 <2.0.0", "2.0.0")
    assert allows("1.0.0 || >=2.0.0", "2.5.0")
    assert not allows("1.0.0 || >=2.0.0", "1.5.0")


def test_wildcards_mean_any_release():
    assert allows("*", "0.0.1")
    assert subject.parse_range("*").any_version()


def test_partial_versions_are_padded_not_guessed():
    assert allows(">=1.2", "1.2.0")
    assert not allows(">=1.2", "1.1.9")


def test_an_unreadable_range_names_itself():
    try:
        subject.parse_range("banana")
    except subject.RangeError as error:
        assert "banana" in str(error)
    else:
        raise AssertionError("banana should not parse")


def test_an_empty_range_is_refused_rather_than_treated_as_any():
    try:
        subject.parse_range("   ")
    except subject.RangeError as error:
        assert "ambiguous" in str(error)
    else:
        raise AssertionError("an empty range should not mean *")
