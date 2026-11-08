"""The demo stories, checked for shape."""

from __future__ import annotations

from {{ package_name }}.demo import stories


def test_six_stories():
    told = stories()
    assert len(told) == 6
    assert all(story.held for story in told)
