from __future__ import annotations

from {{ package_name }}.demo import (
    stories,
)


def test_six_stories_are_told() -> None:
    assert len(stories()) == 6


def test_every_story_holds() -> None:
    for story in stories():
        assert story.held, story.title
