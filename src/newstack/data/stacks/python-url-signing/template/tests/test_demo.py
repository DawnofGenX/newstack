"""The demo is checked, not narrated: every story must still hold."""

from __future__ import annotations

from {{ package_name }} import demo as subject


def test_every_story_holds() -> None:
    broken = [story.title for story in subject.stories() if not story.held]
    assert broken == []


def test_there_are_six_stories() -> None:
    assert len(subject.stories()) == 6


def test_the_rendering_separates_stories() -> None:
    text = subject.render_stories()
    assert text.count("-> holds") == 6
    assert text.startswith("1. ")
