"""The demo tells six stories and every number is computed live."""

from __future__ import annotations

from {{ package_name }}.demo import (
    DEMO_ROWS,
    DEMO_SEED,
    DEMO_WIDTH,
    Story,
    stories,
)


def test_six_stories_are_told() -> None:
    told = stories()
    assert len(told) == 6
    assert all(isinstance(story, Story) for story in told)


def test_every_story_holds() -> None:
    for story in stories():
        assert story.held, story.title
        assert story.detail


def test_the_small_array_shows_the_edge_on_purpose() -> None:
    assert (DEMO_WIDTH, DEMO_ROWS, DEMO_SEED) == (64, 4, 7)
    first = stories()[2]
    assert "only ever answer present" in first.detail
