from __future__ import annotations

from {{ package_name }}.demo import stories


def test_six_stories_are_told() -> None:
    told = stories()
    assert len(told) == 6
    assert {story.title for story in told} == {
        "membership answers what a set answers",
        "every rectangle answer equals the brute-force filter",
        "the nearest answer equals the brute-force argmin",
        "a rebuild from the in-order walk answers identically",
        "a storm keeps every promise after every op",
        "the edges answer: empty and single-point trees",
    }


def test_every_story_holds_with_real_numbers() -> None:
    for story in stories():
        assert story.held, story.title
        assert story.detail


def test_a_story_recounts_the_same_claims() -> None:
    first = stories()
    second = stories()
    assert [story.detail for story in first] == \
        [story.detail for story in second]
