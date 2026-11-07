from __future__ import annotations

from {{ package_name }}.demo import (
    stories,
)


def test_six_stories_are_told() -> None:
    assert len(stories()) == 6


def test_every_story_holds_against_the_live_modules() -> None:
    for story in stories():
        assert story.held, story.title
        assert story.detail


def test_the_stories_stay_told_run_after_run() -> None:
    first = [story.detail for story in stories()]
    second = [story.detail for story in stories()]
    assert first == second
