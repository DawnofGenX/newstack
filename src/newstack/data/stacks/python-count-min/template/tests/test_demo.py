from __future__ import annotations

from {{ package_name }}.demo import stories


def test_six_stories_are_told() -> None:
    told = stories()
    assert len(told) == 6


def test_every_story_holds_on_its_numbers() -> None:
    for story in stories():
        assert story.held, story.title
        assert story.detail


def test_the_stories_are_named_for_the_promise() -> None:
    titles = [story.title for story in stories()]
    assert "the min of rows never dips under the truth" in titles
    assert "an empty sketch counts zero for every key" in titles
    assert "same stream, same seed, same answers" in titles
