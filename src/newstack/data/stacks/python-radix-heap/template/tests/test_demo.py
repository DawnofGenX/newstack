from __future__ import annotations

from {{ package_name }}.demo import render_stories, stories


def test_six_stories_are_told() -> None:
    told = stories()
    assert len(told) == 6
    assert all(story.held for story in told)
    assert all(story.detail for story in told)


def test_the_render_reports_every_story_holding() -> None:
    rendered = render_stories()
    assert "6 of 6 hold" in rendered
    assert "pop-min answers sorted" in rendered
