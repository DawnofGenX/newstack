from __future__ import annotations

from {{ package_name }}.demo import (
    Story,
    stories,
)


def test_six_stories_are_told() -> None:
    assert len(stories()) == 6


def test_every_story_holds() -> None:
    for story in stories():
        assert story.held, story.title


def test_every_story_carries_a_title_and_numbers() -> None:
    for story in stories():
        assert story.title
        assert story.detail
        assert isinstance(story.held, bool)


def test_a_story_is_a_frozen_record() -> None:
    story = Story("a promise", "detail", True)
    assert story.title == "a promise"
    try:
        story.held = False
    except Exception:
        return
    raise AssertionError("a story was rewritten")


def test_the_stories_answer_twice_the_same() -> None:
    first = [story.detail for story in stories()]
    second = [story.detail for story in stories()]
    assert first == second
