from __future__ import annotations

from {{ package_name }}.demo import (
    Story,
    stories,
)


def test_six_stories_are_told() -> None:
    told = stories()
    assert len(told) == 6
    assert all(isinstance(story, Story) for story in told)


def test_every_story_holds_on_its_real_numbers() -> None:
    for story in stories():
        assert story.held, story.detail
        assert story.title
        assert story.detail
