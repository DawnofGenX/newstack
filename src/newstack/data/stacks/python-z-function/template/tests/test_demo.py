from __future__ import annotations

from {{ package_name }}.demo import stories


def test_six_stories_are_told() -> None:
    told = stories()
    assert len(told) == 6
    assert all(story.held for story in told)


def test_every_story_carries_its_numbers() -> None:
    for story in stories():
        assert story.title
        assert story.detail


def test_the_stories_repeat_themselves() -> None:
    first = [(story.title, story.detail) for story in stories()]
    second = [(story.title, story.detail) for story in stories()]
    assert first == second
