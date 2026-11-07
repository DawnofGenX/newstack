from __future__ import annotations

from {{ package_name }}.demo import stories


def test_six_stories_are_told_and_all_hold() -> None:
    told = stories()
    assert len(told) == 6
    for story in told:
        assert story.held, story.title
        assert story.detail


def test_the_stories_recompute_on_every_call() -> None:
    first = stories()
    second = stories()
    assert [story.detail for story in first] == [story.detail for story in second]
