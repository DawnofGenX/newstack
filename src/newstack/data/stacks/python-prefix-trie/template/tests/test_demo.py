from __future__ import annotations

from {{ package_name }}.demo import stories


def test_six_stories_are_told() -> None:
    told = stories()
    assert len(told) == 6
    assert {story.title for story in told} == {
        "membership answers what a set answers",
        "every prefix listing equals the sorted scan",
        "the empty prefix lists every word exactly once",
        "delete drops the word, survivors keep their stems",
        "the common prefix belongs to every word it names",
        "a storm keeps every promise after every op",
    }


def test_every_story_holds_with_real_numbers() -> None:
    for story in stories():
        assert story.held, story.title
        assert story.detail
