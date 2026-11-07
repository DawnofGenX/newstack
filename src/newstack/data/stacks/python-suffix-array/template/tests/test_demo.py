from __future__ import annotations

from {{ package_name }}.demo import stories


def test_six_stories_are_told() -> None:
    told = stories()
    assert len(told) == 6
    assert {story.title for story in told} == {
        "the order is the plain sort, exactly",
        "the count is every start, overlaps honest",
        "two suffixes share what the scan compares",
        "the longest repeat is the tallest share",
        "seeded texts order the way slices sort",
        "empty and single letters answer without complaint",
    }


def test_every_story_holds_with_real_numbers() -> None:
    for story in stories():
        assert story.held, story.title
        assert story.detail
