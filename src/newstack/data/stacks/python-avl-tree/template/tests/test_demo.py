from __future__ import annotations

from {{ package_name }}.demo import (
    stories,
)


def test_six_stories_are_told() -> None:
    told = stories()
    assert len(told) == 6
    assert {story.title for story in told} == {
        "the walk is the plain sort, exactly",
        "every factor sits inside -1, 0, 1",
        "the height stays under the ceiling",
        "a rebuild from the walk answers alike",
        "removal leaves the survivors seated",
        "empty, single, and duplicate keys answer quietly",
    }


def test_every_story_holds_with_real_numbers() -> None:
    for story in stories():
        assert story.held, story.title
        assert story.detail
