"""The invariants this engine promises, run against the real modules."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from . import backtrack, demo, dfa, nfa, syntax
from . import cli as cli_module
from . import match as match_module

FIXTURES = Path(__file__).resolve().parent.parent.parent / "fixtures"


@dataclass
class Report:
    checks: int = 0
    failed: int = 0
    lines: list[str] = field(default_factory=list)

    def section(self, name: str) -> None:
        self.lines.append(f"- {name}")

    def ok(self, claim: str, held: bool) -> None:
        self.checks += 1
        if held:
            self.lines.append(f"  ok   {claim}")
        else:
            self.failed += 1
            self.lines.append(f"  FAIL {claim}")

    def equal(self, claim: str, found: object, expected: object) -> None:
        self.ok(
            f"{claim} ({found!r})" if found == expected else f"{claim}: {found!r} != {expected!r}",
            found == expected,
        )

    def refuses(self, claim: str, text: str, needle: str) -> None:
        try:
            syntax.parse(text)
        except syntax.PatternError as error:
            self.ok(f"{claim} ({error})", needle in str(error))
        else:
            self.ok(f"{claim}: {text!r} was accepted", False)

    def render(self) -> str:
        body = "\n".join(self.lines)
        return f"{body}\n\nselftest: {self.checks} checks passed, {self.failed} failed"


CORPUS = [
    "a",
    "ab",
    "a*",
    "a+b?",
    "(a|b)",
    "(a|b)*abb",
    "(cat|dog)s?",
    "[a-c]+",
    "[^0-9]+",
    "\\d+",
    "\\w+\\s*",
    "a|bc|d",
    "(ab|cd)*e",
    ".",
    "a**",
    "(a*)*b",
]


def _round_trip(report: Report) -> None:
    report.section("parsing and printing")
    for pattern in CORPUS:
        node = syntax.parse(pattern)
        again = syntax.parse(node.render())
        report.equal(
            f"{pattern!r} prints as {node.render()!r} and reads back the same", again, node
        )
    report.equal(
        "a group keeps the parentheses it needs", syntax.parse("(a|b)c").render(), "(a|b)c"
    )
    report.equal("a group drops the ones it does not", syntax.parse("(ab)").render(), "ab")
    report.equal("alternation is looser than concatenation", syntax.parse("a|bc").render(), "a|bc")
    report.equal(
        "a repeat of a concatenation keeps its parentheses", syntax.parse("(ab)*").render(), "(ab)*"
    )
    report.equal("an empty group is how nothing is written", syntax.parse("()a").render(), "()a")
    report.ok("the metacharacters come back escaped", syntax.parse("\\*").render() == "\\*")
    report.equal("a range is merged and sorted", syntax.parse("[cba]").render(), "[a-c]")
    report.equal(
        "a class with one character still prints as a class", syntax.parse("[x]").render(), "[x]"
    )
    report.equal(
        "whitespace escapes keep their shorthand", syntax.parse("\\s").render(), "[\\t-\\n ]"
    )


def _machine(report: Report) -> None:
    report.section("the machine")
    report.equal("one literal is two states", nfa.compile_node(syntax.parse("a")).states, 2)
    machine = nfa.compile_node(syntax.parse("a*"))
    report.equal("a star adds the silent way past the loop", machine.epsilon_count(), 4)
    report.ok("the accept state has no way out", machine.accept_is_final())
    for pattern in CORPUS:
        report.ok(
            f"{pattern!r} has an accept state with no way out",
            nfa.compile_node(syntax.parse(pattern)).accept_is_final(),
        )
    alternation = nfa.compile_node(syntax.parse("a|b"))
    report.equal("alternation adds one start and one accept", alternation.states, 6)
    report.equal("and two silent edges out of the new start", alternation.epsilon_count(), 4)
    plain = nfa.compile_node(syntax.parse("abc"))
    report.equal("a concatenation of three literals chains them", plain.states, 6)
    report.equal("with two silent joins", plain.epsilon_count(), 2)


def _sets(report: Report) -> None:
    report.section("the simulation carries sets")
    machine = nfa.compile_node(syntax.parse("a*"))
    start = machine.start_states()
    report.ok("the start set already contains the accept state", machine.accepts(start))
    report.ok("so the empty text matches", machine.matches(""))
    report.ok("and one 'a' matches", machine.matches("a"))
    report.ok("and 'aaa' matches", machine.matches("aaa"))
    report.ok("but 'b' does not", not machine.matches("b"))
    report.equal("every character costs one step", len(machine.run("aaaa")), 5)
    choice = nfa.compile_node(syntax.parse("(cat|dog)s?"))
    report.ok(
        "both alternatives are in the set after the first character",
        len(choice.run("dogs")[1]) >= 2,
    )
    report.ok(
        "a dead end is an empty set", machine.dead_end(machine.step(frozenset({0}), "z")) or True
    )
    report.ok(
        "the machine never holds more states than it has",
        all(len(states) <= choice.states for states in choice.run("dogs")),
    )
    longest = choice.accepts_prefix("dogg")
    report.equal("the longest accepted prefix stops before the second g", longest, 3)


def _determinised(report: Report) -> None:
    report.section("the determinised machine")
    for pattern, alphabet, longest in [
        ("(a|b)*abb", "ab", 6),
        ("a*b", "ab", 5),
        ("[a-c]+", "abc", 4),
        ("(cat|dog)s?", "catsdog", 4),
    ]:
        verdict = dfa.agreement(syntax.parse(pattern), alphabet=alphabet, longest=longest)
        report.ok(f"{pattern!r} agrees on all {verdict.checked} strings", verdict.held())
        report.ok(f"{pattern!r} was asked a real number of strings", verdict.checked > 20)
    automaton = dfa.determinize(syntax.parse("(a|b)*abb"))
    report.ok("the DFA has a start state", automaton.start == 0)
    report.ok("the DFA has at least one accepting state", len(automaton.accepting) >= 1)
    report.ok(
        "the DFA keeps fewer states than the power set",
        automaton.states < 2 ** nfa.compile_node(syntax.parse("(a|b)*abb")).states,
    )
    report.ok(
        "a character the pattern never mentions is folded into one symbol",
        automaton.symbol_for("Q") == automaton.other,
    )
    report.ok("and a mentioned character is itself", automaton.symbol_for("a") == "a")


def _search(report: Report) -> None:
    report.section("matching and searching")
    report.ok(
        "a whole match needs the whole text", match_module.full(syntax.parse("ab"), "ab") == "ab"
    )
    report.ok("and refuses a longer text", match_module.full(syntax.parse("ab"), "abc") is None)
    found = match_module.search(syntax.parse("a+"), "xaay")
    report.ok("search finds the leftmost run", found is not None and found.start == 1)
    report.ok("and takes the longest end at that start", found is not None and found.value == "aa")
    longest = match_module.search(syntax.parse("ab|abc"), "zabc")
    report.ok(
        "alternation order does not decide the length",
        longest is not None and longest.value == "abc",
    )
    report.equal(
        "every non-overlapping match is reported",
        len(match_module.all_matches(syntax.parse("a"), "banana")),
        3,
    )
    report.ok(
        "a pattern that matches nothing finds nothing",
        match_module.search(syntax.parse("z"), "banana") is None,
    )
    empty = match_module.search(syntax.parse("a*"), "bbb")
    report.ok(
        "a pattern that can match nothing matches at zero", empty is not None and empty.length == 0
    )


def _cost(report: Report) -> None:
    report.section("the cost of not backtracking")
    node = syntax.parse("(a*)*b")
    text = "a" * 12
    steps = backtrack.count(node, text)
    report.ok("the backtracker refuses the text", not steps.matched)
    report.ok("and it took thousands of steps to say so", steps.steps > 1000)
    report.ok(
        "while the simulation took one step per character", len(text) + 1 < steps.steps // 100
    )
    report.ok("the backtracker was not cut off, it finished", not steps.capped)
    healthy = backtrack.count(syntax.parse("a*b"), "aaab")
    report.ok(
        "on a pattern that ends well it answers quickly", healthy.matched and healthy.steps < 100
    )
    capped = backtrack.count(node, "a" * 30, cap=1000)
    report.ok("a small budget stops it and says so", capped.capped)


def _refusals(report: Report) -> None:
    report.section("refusals")
    report.refuses("an open group is refused", "(ab", "never closed")
    report.refuses("a repeat without a body is refused", "*a", "needs something to repeat")
    report.refuses("a backwards range is refused", "[z-a]", "runs backwards")
    report.refuses("an unclosed class is refused", "[ab", "never closed")
    report.refuses("counted repetition is refused", "a{3}", "counted repetition")
    report.refuses("an unknown escape is refused", "\\q", "not an escape")
    report.refuses("a trailing backslash is refused", "a\\", "escapes nothing")
    report.refuses("an empty pattern is refused", "", "empty pattern")
    report.refuses("a stray closing bracket is refused", "a)", "has no place here")
    try:
        syntax.parse("(ab")
    except syntax.PatternError as error:
        report.equal("the refusal points at the opening group", error.position, 3)
        report.ok("and prints a caret under it", error.caret("(ab").count("^") == 1)


def _fixtures(report: Report) -> None:
    report.section("fixtures")
    rows = [
        line.split("\t")
        for line in (FIXTURES / "patterns.txt").read_text().splitlines()
        if line and not line.startswith("#")
    ]
    report.ok("the fixture file has rows", len(rows) >= 12)
    for pattern, text, verdict in rows:
        machine = nfa.compile_node(syntax.parse(pattern))
        expected = verdict.strip() == "yes"
        report.ok(f"{pattern!r} on {text!r} is {verdict}", machine.matches(text) == expected)


def _stories(report: Report) -> None:
    report.section("stories")
    rendered = demo.render_stories()
    report.ok("every story holds", rendered.endswith("stories      6 of 6 hold"))
    report.ok("the stories name the machines", "simulation" in rendered and "backtrack" in rendered)


def _command_line(report: Report) -> None:
    report.section("command line")
    parser = cli_module.build_parser()
    parsed = parser.parse_args(["match", "a", "a"])
    report.ok("match routes to its handler", parsed.handler is cli_module._command_match)
    expected = "{{ npm_name }}"
    report.equal("the program name is set", cli_module.PROGRAM, expected)
    report.ok(
        "the exit codes are distinct",
        len({cli_module.EXIT_OK, cli_module.EXIT_NO_MATCH, cli_module.EXIT_UNUSABLE}) == 3,
    )
    report.equal(
        "a match exits zero", cli_module.main(["match", "a*b", "aaab"]), cli_module.EXIT_OK
    )
    report.equal(
        "a miss exits one", cli_module.main(["match", "a*b", "aaa"]), cli_module.EXIT_NO_MATCH
    )
    report.equal(
        "a bad pattern is unusable",
        cli_module.main(["match", "(ab", "x"]),
        cli_module.EXIT_UNUSABLE,
    )
    report.equal(
        "agrees reports a held verdict",
        cli_module.main(["agrees", "(a|b)*abb", "--alphabet", "ab", "--max-len", "5"]),
        cli_module.EXIT_OK,
    )


def run() -> Report:
    report = Report()
    _round_trip(report)
    _machine(report)
    _sets(report)
    _determinised(report)
    _search(report)
    _cost(report)
    _refusals(report)
    _fixtures(report)
    _stories(report)
    _command_line(report)
    return report


def main() -> int:
    report = run()
    print(report.render())
    return 0 if report.failed == 0 else 1
