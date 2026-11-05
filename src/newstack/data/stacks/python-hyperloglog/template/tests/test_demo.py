from __future__ import annotations

from {{ package_name }} import demo as subject


def test_every_story_holds() -> None:
    for story in subject.stories():
        assert story.held, story.title


def test_the_six_titles_are_the_six_claims() -> None:
    titles = [story.title for story in subject.stories()]
    assert len(titles) == 6
    assert titles[0].startswith("1. an estimate beside the memory")
    assert titles[5].startswith("6. precision buys accuracy")


def test_the_merge_story_shows_that_summing_is_wrong() -> None:
    story = subject.merge_story()
    joined = "\n".join(story.lines)
    assert "union is max, not sum" in joined


def test_the_bias_story_names_the_collapse() -> None:
    story = subject.bias_story()
    joined = "\n".join(story.lines)
    assert "register 0" in joined
    assert story.held


def test_the_rendered_demo_lists_every_story() -> None:
    text = subject.render()
    assert text.count("-> holds") == 6
    assert "BROKEN" not in text
