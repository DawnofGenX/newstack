from __future__ import annotations

from {{ package_name }}.demo import (
    Story,
    stories,
)


def test_six_stories_are_told_and_every_one_holds() -> None:
    told = stories()
    assert len(told) == 6
    assert all(isinstance(story, Story) for story in told)
    assert all(story.held for story in told)


def test_a_story_carries_a_title_and_real_numbers() -> None:
    for story in stories():
        assert story.title
        assert story.detail
        assert isinstance(story.held, bool)


def test_the_stories_answer_twice_the_same() -> None:
    first = stories()
    second = stories()
    assert [(s.title, s.detail, s.held) for s in first] == [
        (s.title, s.detail, s.held) for s in second
    ]
