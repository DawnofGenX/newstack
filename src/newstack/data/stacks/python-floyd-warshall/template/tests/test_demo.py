from __future__ import annotations

from {{ package_name }}.demo import (
    Story,
    stories,
)


def test_six_stories_are_told() -> None:
    assert len(stories()) == 6


def test_every_story_holds_against_the_live_modules() -> None:
    for story in stories():
        assert story.held, story.title


def test_every_story_carries_its_numbers() -> None:
    for story in stories():
        assert story.title
        assert story.detail


def test_a_story_is_frozen_once_told() -> None:
    story = Story("a promise", "numbers", True)
    assert story.held
    try:
        story.held = False
    except Exception:
        pass
    else:
        raise AssertionError("a story moved after telling")
