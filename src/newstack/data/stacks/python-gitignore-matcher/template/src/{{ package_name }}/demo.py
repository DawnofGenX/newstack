"""Six stories about the rules behind a .gitignore line."""

from __future__ import annotations

from dataclasses import dataclass, field

from .matcher import Matcher


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


def _matcher(rules: list[str]) -> Matcher:
    matcher, _ = Matcher.from_lines(rules)
    return matcher


def story_one() -> Story:
    story = Story(1, "the last rule that matches is the one that decides")
    matcher = _matcher(["*.log", "!keep.log"])
    story.say("rules   *.log, !keep.log")
    story.say(f"debug.log  ignored={matcher.ignored('debug.log')}")
    story.say(f"keep.log   ignored={matcher.ignored('keep.log')}")
    story.require("the general rule ignores a log", matcher.ignored("debug.log"))
    story.require("the later negation rescues one name", not matcher.ignored("keep.log"))
    reversed_matcher = _matcher(["!keep.log", "*.log"])
    reversed_order = reversed_matcher.ignored("keep.log")
    story.say(f"order matters: !keep.log then *.log ignores keep.log={reversed_order}")
    story.require("reversing the order reverses the answer", reversed_matcher.ignored("keep.log"))
    return story


def story_two() -> Story:
    story = Story(2, "a slash anchors; a bare name matches at any depth")
    anywhere = _matcher(["build"])
    rooted = _matcher(["/build"])
    story.say(f"rule build    sub/build ignored={anywhere.ignored('sub/build', is_dir=True)}")
    story.say(f"rule /build   sub/build ignored={rooted.ignored('sub/build', is_dir=True)}")
    story.require("a bare name matches anywhere", anywhere.ignored("sub/build", is_dir=True))
    nested = rooted.ignored("sub/build", is_dir=True)
    story.require("a leading slash pins it to the root", not nested)
    story.require("the root still matches", rooted.ignored("build", is_dir=True))
    return story


def story_three() -> Story:
    story = Story(3, "a trailing slash names a directory, and its contents follow")
    matcher = _matcher(["build/"])
    story.say(f"build as a file      ignored={matcher.ignored('build')}")
    story.say(f"build as a directory ignored={matcher.ignored('build', is_dir=True)}")
    verdict = matcher.decide("build/out/app.js")
    story.say(f"build/out/app.js     ignored={verdict.ignored} via {verdict.parent}")
    story.require("a file named build is not a directory", not matcher.ignored("build"))
    story.require("the directory is ignored", matcher.ignored("build", is_dir=True))
    story.require("its contents go with it", verdict.ignored and verdict.parent == "build")
    return story


def story_four() -> Story:
    story = Story(4, "one star stops at a slash; two stars do not")
    shallow = _matcher(["logs/*.log"])
    deep = _matcher(["logs/**/*.log"])
    story.say(f"logs/*.log      logs/a.log ignored={shallow.ignored('logs/a.log')}")
    story.say(f"logs/*.log      logs/x/a.log ignored={shallow.ignored('logs/x/a.log')}")
    story.say(f"logs/**/*.log   logs/x/a.log ignored={deep.ignored('logs/x/a.log')}")
    story.require("a single star reaches one level", shallow.ignored("logs/a.log"))
    story.require("a single star stops at the slash", not shallow.ignored("logs/x/a.log"))
    story.require("two stars cross directories", deep.ignored("logs/x/a.log"))
    return story


def story_five() -> Story:
    story = Story(5, "question marks, classes and escapes")
    matcher = _matcher(["file[0-9].txt", "temp?.md", "\\#notes"])
    story.say("rules   file[0-9].txt, temp?.md, \\#notes")
    story.require("a class matches one character in the range", matcher.ignored("file7.txt"))
    story.require("a class does not match two", not matcher.ignored("file77.txt"))
    story.require("a question mark matches exactly one", matcher.ignored("tempA.md"))
    story.require("a question mark does not match nothing", not matcher.ignored("temp.md"))
    story.require("an escaped hash is a name, not a comment", matcher.ignored("#notes"))
    return story


def story_six() -> Story:
    story = Story(6, "a negation cannot rescue a file inside an excluded directory")
    matcher = _matcher(["build/", "!build/keep.txt"])
    verdict = matcher.decide("build/keep.txt")
    story.say("rules   build/, !build/keep.txt")
    story.say(f"build/keep.txt ignored={verdict.ignored}")
    story.say(f"reason  {verdict.reason}")
    story.require("the negation is not enough", verdict.ignored)
    story.require("the reason names the parent", verdict.parent == "build")
    reachable = _matcher(["build/*", "!build/keep.txt"])
    story.say(f"with build/* instead, build/keep.txt ignored={reachable.ignored('build/keep.txt')}")
    rescued = reachable.ignored("build/keep.txt")
    story.require("a rule that names the files can be undone", not rescued)
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
