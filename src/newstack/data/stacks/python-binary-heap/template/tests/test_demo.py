from __future__ import annotations

from {{ package_name }}.demo import (
    stories,
)


def test_six_stories_are_told_and_all_hold() -> None:
    told = stories()
    assert len(told) == 6
    for story in told:
        assert story.held, story.title


def test_every_story_carries_numbers() -> None:
    for story in stories():
        assert story.title
        assert story.detail
