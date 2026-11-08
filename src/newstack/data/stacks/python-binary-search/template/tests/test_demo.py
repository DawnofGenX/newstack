"""The demo stories, checked for shape."""

from __future__ import annotations

from {{ package_name }}.demo import stories


def test_six_stories():
    told = stories()
    assert len(told) == 6
    assert all(story.held for story in told)


def test_story_titles():
    told = stories()
    titles = [s.title for s in told]
    assert "a hit answers its index" in titles
