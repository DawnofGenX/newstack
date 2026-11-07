from __future__ import annotations

from {{ package_name }}.demo import render_stories, stories


def test_six_stories_are_told() -> None:
    told = stories()
    assert len(told) == 6
    for story in told:
        assert story.held, story.title


def test_the_render_reports_every_story(capsys) -> None:
    report = render_stories()
    assert report.endswith("6 of 6 hold")
    assert "meld" in report
    assert "2^6" in report
