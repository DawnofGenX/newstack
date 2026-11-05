import pytest

from {{ package_name }} import patterns


def test_one_star_covers_exactly_one_segment():
    assert patterns.matches("project:*", "project:acme")
    assert not patterns.matches("project:*", "project:acme/doc:42")


def test_a_star_inside_a_segment_is_a_glob():
    assert patterns.matches("docs:*", "docs:read", ":")
    assert not patterns.matches("docs:*", "comments:read", ":")


def test_two_stars_reach_the_bottom():
    assert patterns.matches("project:**", "project:acme/doc:42")
    assert patterns.matches("**/secret", "project:acme/secret")
    assert patterns.matches("**", "project:acme/secret")


def test_a_literal_path_matches_itself_only():
    assert patterns.matches("project:acme/*", "project:acme/doc:42")
    assert not patterns.matches("project:acme/*", "project:other/doc:42")


def test_matching_is_case_sensitive():
    assert not patterns.matches("Project:acme", "project:acme")


def test_an_empty_segment_is_refused():
    with pytest.raises(patterns.PatternError):
        patterns.segments("policy//docs")


def test_an_empty_pattern_is_refused():
    with pytest.raises(patterns.PatternError):
        patterns.segments("")


def test_a_scope_covers_itself_and_children():
    assert patterns.scoped("project:acme", "project:acme")
    assert patterns.scoped("project:acme", "project:acme/doc:42")


def test_a_scope_does_not_cover_a_sibling():
    assert not patterns.scoped("project:acme", "project:acme2/doc:1")
    assert not patterns.scoped("project:acme", "project:other/doc:1")


def test_no_scope_covers_everything():
    assert patterns.scoped(None, "project:other/doc:1")


def test_depth_counts_segments():
    assert patterns.depth("project:acme/*") == 2
    assert patterns.depth("project:acme/doc:42") == 2
    assert patterns.depth("project:acme/doc:42/comments") == 3
