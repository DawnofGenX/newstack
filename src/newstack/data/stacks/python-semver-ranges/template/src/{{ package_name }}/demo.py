"""Six stories that make the rules behind a version range visible."""

from __future__ import annotations

from dataclasses import dataclass, field

from .explain import decide
from .ranges import Range, intersect, parse_range
from .version import Version, parse


@dataclass
class Story:
    number: int
    title: str
    lines: list[str] = field(default_factory=list)
    claims: list[tuple[str, bool]] = field(default_factory=list)

    def say(self, text: str) -> None:
        self.lines.append(f"  {text}")

    def require(self, claim: str, held: bool) -> None:
        self.claims.append((claim, held))
        self.lines.append(f"  {claim}: {'yes' if held else 'NO'}")

    def held(self) -> bool:
        return all(held for _, held in self.claims)


def _names(versions: list[Version]) -> str:
    return " < ".join(str(version) for version in versions)


def _arms(chosen: Range) -> str:
    return chosen.render()


def story_one() -> Story:
    story = Story(1, "a version is ordered fields, not a decimal number")
    versions = [parse("1.10.0"), parse("1.9.0"), parse("1.2.0")]
    ordered = sorted(versions)
    story.say("as decimals  1.10.0 > 1.9.0, because 10 > 9")
    story.say(f"as versions  {_names(ordered)}")
    story.require("1.10.0 sorts above 1.9.0", ordered[-1] == parse("1.10.0"))
    chain = [parse("1.0.0-alpha"), parse("1.0.0-alpha.1"), parse("1.0.0-beta"), parse("1.0.0")]
    story.say(f"prereleases  {_names(chain)}")
    story.require("a prerelease sorts below its release", chain == sorted(chain))
    story.say(f"1.0.0+left == 1.0.0+right: {parse('1.0.0+left') == parse('1.0.0+right')}")
    story.require(
        "build metadata does not take part in precedence",
        parse("1.0.0+left") == parse("1.0.0+right"),
    )
    return story


def story_two() -> Story:
    story = Story(2, "caret is three rules wearing one hat")
    cases = [
        ("^1.2.3", "1.9.9", "2.0.0"),
        ("^0.2.3", "0.2.9", "0.3.0"),
        ("^0.0.3", "0.0.3", "0.0.4"),
    ]
    for text, inside, outside in cases:
        chosen = parse_range(text)
        story.say(f"{text:<8} {_arms(chosen)}")
        story.require(
            f"{text} allows {inside} and refuses {outside}",
            chosen.allows(parse(inside)) and not chosen.allows(parse(outside)),
        )
    return story


def story_three() -> Story:
    story = Story(3, "a partial version is an interval, not a wildcard string")
    cases = [
        ("1.2", "1.2.99", "1.3.0"),
        ("1", "1.9.9", "2.0.0"),
        (">1.2", "1.3.0", "1.2.9"),
        ("<=1.2", "1.2.99", "1.3.0"),
    ]
    for text, inside, outside in cases:
        chosen = parse_range(text)
        story.say(f"{text:<8} {_arms(chosen)}")
        story.require(
            f"{text} allows {inside} and refuses {outside}",
            chosen.allows(parse(inside)) and not chosen.allows(parse(outside)),
        )
    story.say(f"*        {_arms(parse_range('*'))}")
    story.require("a bare wildcard allows a release", parse_range("*").allows(parse("7.3.1")))
    return story


def story_four() -> Story:
    story = Story(4, "hyphen ranges and || arms are intervals you can read")
    hyphen = parse_range("1.2 - 2.3.4")
    story.say(f"1.2 - 2.3.4   {_arms(hyphen)}")
    story.require(
        "the hyphen start is the lowest 1.2 version",
        hyphen.allows(parse("1.2.0")) and not hyphen.allows(parse("1.1.9")),
    )
    story.require("the hyphen end is inclusive here", hyphen.allows(parse("2.3.4")))
    union = parse_range("~1.4 || ^2.0")
    story.say(f"~1.4 || ^2.0  {_arms(union)}")
    story.require(
        "either arm is enough",
        union.allows(parse("1.4.9")) and union.allows(parse("2.5.0")),
    )
    story.require("the gap between the arms is real", not union.allows(parse("1.9.0")))
    return story


def story_five() -> Story:
    story = Story(5, "a prerelease is opt-in, and only where it is named")
    caret = parse_range("^1.2.0")
    story.say(f"^1.2.0        {_arms(caret)}")
    beta_refused = not caret.allows(parse("1.3.0-beta"))
    story.require("a caret range does not opt into prereleases", beta_refused)
    named = parse_range(">=1.3.0-beta <2")
    story.say(f">=1.3.0-beta <2  {_arms(named)}")
    story.require("a named prerelease is allowed", named.allows(parse("1.3.0-beta")))
    story.require(
        "another core's prerelease is still refused",
        not named.allows(parse("1.4.0-rc.1")),
    )
    return story


def story_six() -> Story:
    story = Story(6, "two ranges meet in a place you can point at, or nowhere")
    narrow = intersect(parse_range("^1.2.3"), parse_range(">=1.4.0 <1.5.0"))
    story.say(f"^1.2.3 && >=1.4.0 <1.5.0  {_arms(narrow) if narrow else 'empty'}")
    story.require("the overlap keeps the tighter bound", narrow is not None)
    story.require(
        "and it is exactly the tighter interval",
        narrow is not None
        and narrow.allows(parse("1.4.0"))
        and not narrow.allows(parse("1.5.0"))
        and not narrow.allows(parse("1.3.9")),
    )
    empty = intersect(parse_range("^1.0"), parse_range("^2.0"))
    story.say(f"^1.0 && ^2.0              {_arms(empty) if empty else 'empty'}")
    story.require("disjoint ranges have no overlap", empty is None)
    decision = decide(parse("1.5.0"), parse_range("~1.4 || ^2.0"))
    story.say("why 1.5.0 fails ~1.4 || ^2.0:")
    for line in decision.lines()[2:]:
        story.say(line.strip())
    explained = not decision.ok and len(decision.reasons) == 2
    story.require("the refusal is explained arm by arm", explained)
    return story


def stories() -> list[Story]:
    return [story_one(), story_two(), story_three(), story_four(), story_five(), story_six()]


def render_stories() -> list[str]:
    lines: list[str] = []
    total = 0
    held = 0
    for story in stories():
        total += 1
        if story.held():
            held += 1
        lines.append(f"{story.number}. {story.title}")
        lines.extend(story.lines)
        lines.append(f"  -> {'holds' if story.held() else 'BROKEN'}")
        lines.append("")
    if held == total:
        lines.append(f"stories      {total} of {total} hold")
    else:
        lines.append(f"stories      BROKEN: {total - held} of {total} do not hold")
    return lines


def run() -> int:
    for line in render_stories():
        print(line)
    return 0 if all(story.held() for story in stories()) else 1
