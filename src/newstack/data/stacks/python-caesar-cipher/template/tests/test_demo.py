from __future__ import annotations

from {{ package_name }}.demo import (
    Story,
    stories,
)


def test_six_stories_are_told() -> None:
    assert len(stories()) == 6


def test_every_story_holds_on_its_own() -> None:
    for story in stories():
        assert story.held, story.title


def test_every_story_carries_numbers() -> None:
    for story in stories():
        assert story.detail


def test_a_story_is_frozen_once_told() -> None:
    story = stories()[0]
    assert isinstance(story, Story)
    try:
        story.title = "retold"
    except Exception:
        return
    raise AssertionError("a story rewrote itself")
