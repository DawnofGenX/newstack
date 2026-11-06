"""The demo is a gate: a broken rule turns a story into `-> BROKEN`."""

from __future__ import annotations

from {{ package_name }} import demo as subject


def test_every_story_holds() -> None:
    broken = [story.title for story in subject.stories() if not story.held]
    assert broken == []


def test_the_six_titles_are_the_documented_ones() -> None:
    titles = [story.title for story in subject.stories()]
    assert titles == [
        "1. an inclusion proof recomputes the root",
        "2. a changed leaf cannot produce the same root",
        "3. without a domain prefix, a node passes as a leaf",
        "4. a proof belongs to one index of one tree",
        "5. the empty and single-leaf trees still answer",
        "6. the tree's shape is part of the root",
    ]


def test_every_story_prints_something() -> None:
    for story in subject.stories():
        assert story.lines, story.title
        assert all(line.strip() for line in story.lines), story.title


def test_the_render_marks_each_verdict() -> None:
    rendered = subject.render_stories()
    assert rendered.count("-> holds") == 6
    assert "-> BROKEN" not in rendered


def test_the_shape_story_reports_two_different_roots() -> None:
    shape = next(story for story in subject.stories() if story.title.startswith("6."))
    assert "same root      False" in "\n".join(shape.lines)
