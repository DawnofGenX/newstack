"""Six stories about the two machines and the number that separates them."""

from __future__ import annotations

from . import backtrack, dfa, match, nfa, syntax


class Story:
    def __init__(self, title: str) -> None:
        self.title = title
        self.lines: list[str] = []
        self.failed = 0

    def say(self, text: str) -> None:
        self.lines.append(f"  {text}")

    def block(self, lines: list[str]) -> None:
        for line in lines:
            self.lines.append(f"  {line}")

    def require(self, claim: str, held: bool) -> None:
        mark = "ok  " if held else "FAIL"
        self.lines.append(f"  {mark} {claim}")
        if not held:
            self.failed += 1

    def held(self) -> bool:
        return self.failed == 0

    def render(self) -> str:
        body = "\n".join(self.lines)
        return f"{self.title}\n{body}"


def _story_one() -> Story:
    story = Story("1. the star is silent when it is not needed")
    node = syntax.parse("a*b")
    machine = nfa.compile_node(node)
    story.say("a*b on 'aaab': the star's exit is an epsilon edge, so the machine")
    story.say("leaves the loop without consuming a character.")
    story.block(explain_free(machine, "aaab"))
    story.require("the text matches", machine.matches("aaab"))
    story.require("dropping the b does not match", not machine.matches("aaa"))
    story.require(
        "so the run ended in a set that still held the loop",
        len(machine.run("aaa")[-1]) >= 1,
    )
    return story


def explain_free(machine: nfa.Nfa, text: str) -> list[str]:
    """One row per character: the state set carries itself, no options are lost."""
    rows = []
    sets = machine.run(text)
    for index, char in enumerate(text):
        before = sorted(sets[index])
        after = sorted(sets[index + 1])
        rows.append(f"{char!r}: {before} -> {after}")
    return rows


def _story_two() -> Story:
    story = Story("2. one set, not one guess")
    node = syntax.parse("(cat|dog)s?")
    machine = nfa.compile_node(node)
    sets = machine.run("dogs")
    story.say("(cat|dog)s? on 'dogs': after 'd' both alternatives are still alive,")
    story.say("because the machine keeps every reachable state instead of choosing.")
    story.block(explain_free(machine, "dogs"))
    story.require("the text matches", machine.matches("dogs"))
    story.require("both alternatives were carried at once", len(sets[1]) >= 2)
    story.require("a plain 'cat' matches too", machine.matches("cat"))
    story.require("two s characters do not", not machine.matches("dogss"))
    return story


def _story_three() -> Story:
    story = Story("3. `(a*)*b` costs the simulation one pass")
    node = syntax.parse("(a*)*b")
    machine = nfa.compile_node(node)
    text = "a" * 14
    steps = backtrack.count(node, text)
    story.say("(a*)*b on fourteen a's and no b: the answer is no, and how you ask")
    story.say("decides what saying no costs.")
    story.block([steps.line()])
    story.block(
        [
            f"simulation {len(text) + 1} set(s), one per character plus the start",
            f"machine    {machine.states} state(s), never more than that in one set",
        ]
    )
    story.require("the platform agrees the text does not match", not machine.matches(text))
    story.require("the backtracker also says no", not steps.matched)
    story.require(
        "but it took a hundred times as many steps to say it",
        steps.steps > 100 * (len(text) + 1),
    )
    return story


def _story_four() -> Story:
    story = Story("4. the DFA is the same machine, asked earlier")
    node = syntax.parse("(a|b)*abb")
    machine = nfa.compile_node(node)
    automaton = dfa.determinize(node)
    verdict = dfa.agreement(node, alphabet="ab", longest=6)
    story.say("(a|b)*abb: the subset construction answers every question in advance,")
    story.say("so running the DFA is one table lookup per character.")
    story.block(
        [
            f"nfa        {machine.states} state(s)",
            f"dfa        {automaton.states} state(s), {len(automaton.accepting)} accepting",
        ]
    )
    story.block(verdict.lines())
    story.require("every string they were asked about got the same answer", verdict.held())
    story.require("the check was exhaustive, not sampled", verdict.checked >= 100)
    story.require(
        "and the DFA is smaller than the set of all subsets", automaton.states < 2**machine.states
    )
    return story


def _story_five() -> Story:
    story = Story("5. leftmost first, then longest")
    first = match.search(syntax.parse("ab|abc"), "zabc")
    second = match.search(syntax.parse("a+"), "xaay")
    story.say("The order of alternatives in the pattern does not decide how much")
    story.say("text is taken; leftmost start and longest end do.")
    story.block(
        [
            f"search ab|abc in 'zabc' -> {first.value!r} at [{first.start}, {first.end})"
            if first
            else "search ab|abc in 'zabc' -> nothing",
            f"search a+ in 'xaay'     -> {second.value!r} at [{second.start}, {second.end})"
            if second
            else "search a+ in 'xaay' -> nothing",
        ]
    )
    story.require(
        "the shorter alternative is not chosen first", first is not None and first.value == "abc"
    )
    story.require("the longest run of a's is taken", second is not None and second.value == "aa")
    story.require(
        "the start offset is where the match begins", second is not None and second.start == 1
    )
    return story


def _story_six() -> Story:
    story = Story("6. a refused pattern says where it stopped")
    cases = [
        ("(ab", "a group is open and never closed"),
        ("*a", "'*' needs something to repeat or close"),
        ("[z-a]", "runs backwards"),
        ("a{3}", "counted repetition is not in this engine"),
        ("\\q", "is not an escape this engine knows"),
    ]
    story.say("Every refusal names the position, and a caret points at it.")
    for pattern, expected in cases:
        try:
            syntax.parse(pattern)
        except syntax.PatternError as error:
            story.lines.append(f"  {pattern!r:<8} {error}")
            story.require(f"{pattern!r} is refused for the stated reason", expected in str(error))
        else:
            story.require(f"{pattern!r} should have been refused", False)
    return story


def stories() -> list[Story]:
    return [
        _story_one(),
        _story_two(),
        _story_three(),
        _story_four(),
        _story_five(),
        _story_six(),
    ]


def render_stories() -> str:
    rendered = [story.render() for story in stories()]
    held = sum(1 for story in stories() if story.held())
    total = len(rendered)
    footer = (
        f"stories      {held} of {total} hold"
        if held == total
        else f"stories      BROKEN, {total - held} of {total} do not hold"
    )
    return "\n\n".join(rendered) + "\n\n" + footer
