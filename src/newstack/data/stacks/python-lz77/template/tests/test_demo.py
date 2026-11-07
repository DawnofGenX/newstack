from __future__ import annotations

from {{ package_name }}.demo import (
    Story,
    stories,
)


def test_six_stories_are_told_and_all_hold() -> None:
    told = stories()
    assert len(told) == 6
    assert all(isinstance(story, Story) for story in told)
    assert all(story.held for story in told)


def test_every_story_carries_its_numbers() -> None:
    for story in stories():
        assert story.title
        assert story.detail
