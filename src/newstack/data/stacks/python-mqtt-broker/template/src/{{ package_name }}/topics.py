"""Topic names, topic filters and the wildcard matching between them."""

from __future__ import annotations

from .packet import ProtocolError

MAX_TOPIC = 65_535 - 2


def valid_topic_name(topic: str) -> bool:
    """A publish topic: no wildcards, no length-prefix bytes, not empty."""
    if not topic or len(topic.encode("utf-8")) > MAX_TOPIC:
        return False
    return "+" not in topic and "#" not in topic and "\x00" not in topic


def valid_filter(pattern: str) -> bool:
    if not pattern or len(pattern.encode("utf-8")) > MAX_TOPIC or "\x00" in pattern:
        return False
    levels = pattern.split("/")
    for index, level in enumerate(levels):
        if "#" in level and (level != "#" or index != len(levels) - 1):
            return False
        if "+" in level and level != "+":
            return False
    return True


def matches(pattern: str, topic: str) -> bool:
    """Does this subscription filter cover this publish topic?

    `+` covers exactly one level (including an empty one), `#` covers the rest
    of the tree *and* the parent level itself, which is why `a/#` matches `a`
    as well as `a/b/c`.
    """
    if pattern == topic:
        return True
    p_levels = pattern.split("/")
    t_levels = topic.split("/")
    if p_levels and p_levels[0] == "" and t_levels and t_levels[0] == "":
        pass  # a leading slash is a real, empty level in both
    for index, level in enumerate(p_levels):
        if level == "#":
            return True
        if index >= len(t_levels):
            # `a/#` also matches the parent name `a`.
            return level == "#"
        if level != "+" and level != t_levels[index]:
            return False
    return len(p_levels) == len(t_levels)


def check_publish_topic(topic: str) -> str:
    if not valid_topic_name(topic):
        raise ProtocolError(f"{topic!r} is not a valid publish topic")
    return topic
