"""The stories: six promises, every figure computed live."""

from __future__ import annotations

from {{ package_name }}.demo import stories


def test_six_stories_are_told():
    assert len(stories()) == 6


def test_every_story_holds():
    for story in stories():
        assert story.held, story.title
