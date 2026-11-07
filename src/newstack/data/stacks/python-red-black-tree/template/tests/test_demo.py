from __future__ import annotations

from {{ package_name }}.check import holds
from {{ package_name }}.demo import stories
from {{ package_name }}.tree import RBTree


def test_six_stories_are_told_and_every_one_holds() -> None:
    told = stories()
    assert len(told) == 6
    assert all(story.held for story in told)
    assert all(story.title and story.detail for story in told)


def test_a_story_survives_a_rebuild() -> None:
    tree = RBTree([5, 1, 9])
    rebuilt = RBTree(tree.keys())
    assert rebuilt.keys() == tree.keys()
    assert rebuilt.invariant() and holds(rebuilt._root)
