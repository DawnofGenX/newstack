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
        assert story.title


def test_a_story_is_a_promise_and_its_numbers() -> None:
    story = Story("a promise", "n=1", True)
    assert story.held
    assert story.detail == "n=1"
