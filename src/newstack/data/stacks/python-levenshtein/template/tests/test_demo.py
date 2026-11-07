from __future__ import annotations

from {{ package_name }}.demo import stories


def test_six_stories_are_told_and_every_one_holds() -> None:
    told = stories()
    assert len(told) == 6
    assert all(story.held for story in told)


def test_each_story_carries_a_title_and_numbers() -> None:
    for story in stories():
        assert story.title
        assert story.detail
