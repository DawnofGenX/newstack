from __future__ import annotations

from {{ package_name }}.demo import (
    stories,
)


def test_six_stories_are_told() -> None:
    told = stories()
    assert len(told) == 6
    assert {story.title for story in told} == {
        "every seek equals the scan, all universe",
        "the walk is the plain sort, exactly",
        "removal leaves the survivors seated",
        "a rebuild from the walk answers alike",
        "empty and edge answers come back None, honestly",
        "the full universe seats all two hundred fifty-six",
    }


def test_every_story_holds_with_real_numbers() -> None:
    for story in stories():
        assert story.held, story.title
        assert story.detail
