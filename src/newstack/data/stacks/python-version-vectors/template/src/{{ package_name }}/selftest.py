"""In-process checks: the rules, exercised without a test runner."""

from __future__ import annotations

import io
from contextlib import redirect_stderr, redirect_stdout

from . import causal, lamport, prune
from . import cli as cli_module
from .vector import Relation, VectorError, VersionVector, explain, merge_all


class Report:
    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0
        self.notes: list[str] = []

    def ok(self, name: str, condition: bool, detail: str = "") -> None:
        if condition:
            self.passed += 1
        else:
            self.failed += 1
            self.notes.append(f"FAIL {name}{': ' + detail if detail else ''}")

    def refuses(self, name: str, kind: type[BaseException], action) -> None:
        try:
            action()
        except kind:
            self.passed += 1
        except Exception as error:
            self.failed += 1
            self.notes.append(f"FAIL {name}: raised {type(error).__name__}, not {kind.__name__}")
        else:
            self.failed += 1
            self.notes.append(f"FAIL {name}: nothing was raised")


def _quiet(action):
    """Run a command line without letting its output reach the report."""
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = action()
    return code, out.getvalue(), err.getvalue()


def _vectors(report: Report) -> None:
    report.ok("the empty vector has no nodes", len(VersionVector.empty()) == 0)
    report.ok(
        "an empty string parses to the empty vector",
        VersionVector.parse("") == VersionVector.empty(),
    )
    report.ok("a counter can be added", VersionVector.parse("a:2").increment("a").text() == "a:3")
    report.ok("a new node starts at one", VersionVector.empty().increment("z").text() == "z:1")
    report.ok("text is sorted by name", VersionVector({"b": 1, "a": 2}).text() == "a:2,b:1")
    report.ok("an absent node reads as zero", VersionVector({"a": 1}).get("b") == 0)
    report.ok("total adds the counters", VersionVector({"a": 2, "b": 3}).total() == 5)

    left, right = VersionVector.parse("a:1"), VersionVector.parse("b:1")
    report.ok("two independent writes are concurrent", left.compare(right) is Relation.CONCURRENT)
    report.ok("concurrent is symmetric", right.compare(left) is Relation.CONCURRENT)
    report.ok(
        "the same vector is equal to itself",
        left.compare(VersionVector.parse("a:1")) is Relation.EQUAL,
    )
    report.ok(
        "a smaller counter is before", left.compare(VersionVector.parse("a:2")) is Relation.BEFORE
    )
    report.ok(
        "a larger counter is after", VersionVector.parse("a:2").compare(left) is Relation.AFTER
    )
    report.ok("before is not after", not VersionVector.parse("a:2").before(left))
    report.ok("an empty vector is before any non-empty one", VersionVector.empty().before(left))
    report.ok(
        "a vector with an extra node is after",
        VersionVector.parse("a:1,b:1").compare(left) is Relation.AFTER,
    )

    report.ok("the explanation names the direction", "ahead on the right" in explain(left, right))
    report.ok("an equal pair explains itself", "same counters" in explain(left, left))
    report.ok("a before pair names the counter", "0 -> 1" in explain(VersionVector.empty(), left))

    report.refuses(
        "a duplicate node is refused", VectorError, lambda: VersionVector.parse("a:1,a:2")
    )
    report.refuses("a missing counter is refused", VectorError, lambda: VersionVector.parse("a"))
    report.refuses("a negative counter is refused", VectorError, lambda: VersionVector({"a": -1}))
    report.refuses("a bool counter is refused", VectorError, lambda: VersionVector({"a": True}))
    report.refuses("an empty node name is refused", VectorError, lambda: VersionVector.parse(":1"))
    report.refuses(
        "a colon in a node name is refused", VectorError, lambda: VersionVector({"a:b": 1})
    )


def _lamport(report: Report) -> None:
    clock = lamport.LamportClock("a")
    first = clock.tick()
    second = clock.tick()
    report.ok("a tick moves the clock", second.time == first.time + 1)
    report.ok("a stamp prints its time and node", first.text() == "0001@a")

    receiver = lamport.LamportClock("b")
    received = receiver.receive(lamport.Stamp(7, "a"))
    report.ok("a receive is later than the message", received.time == 8)
    report.ok(
        "a receive is later than anything local",
        lamport.LamportClock("b").receive(second).time == 3,
    )

    draft = lamport.Event("draft", lamport.busy("a", 2).tick())
    idle = lamport.Event("comment", lamport.LamportClock("b").tick())
    busy = lamport.Event("comment", lamport.busy("b", 5).tick())
    report.ok("idle work puts the comment first", lamport.precedes(idle, draft))
    report.ok("busy work puts the draft first", lamport.precedes(draft, busy))
    report.ok(
        "the order flips with unrelated work",
        lamport.precedes(idle, draft) and lamport.precedes(draft, busy),
    )
    report.ok("a clock reports what it counted", lamport.busy("c", 3).ticks == 3)

    report.refuses("an empty order is refused", lamport.LamportError, lambda: lamport.order([]))
    report.refuses(
        "a negative stamp is refused", lamport.LamportError, lambda: lamport.Stamp(-1, "a")
    )
    report.refuses("a stamp needs a node", lamport.LamportError, lambda: lamport.Stamp(1, ""))
    report.refuses(
        "a busy clock refuses a negative count", lamport.LamportError, lambda: lamport.busy("a", -1)
    )


def _laws(report: Report) -> None:
    a = VersionVector({"a": 2, "b": 1})
    b = VersionVector({"b": 3, "c": 1})
    c = VersionVector({"a": 1, "c": 4})
    joined = a.merge(b).merge(c)
    report.ok("merge is idempotent", joined.merge(joined) == joined)
    report.ok("merge is commutative", a.merge(b) == b.merge(a))
    report.ok("merge is associative", a.merge(b).merge(c) == a.merge(b.merge(c)))
    report.ok("merge ignores order across a list", merge_all([a, b, c]) == merge_all([c, a, b]))
    report.ok("the merge is after its arguments", joined.compare(a) is Relation.AFTER)
    report.ok("the merge of a vector with itself is itself", a.merge(a) == a)
    report.ok("merging with empty changes nothing", a.merge(VersionVector.empty()) == a)
    report.ok("an empty list merges to empty", merge_all([]) == VersionVector.empty())
    report.ok("the merged width is the union of names", len(joined) == 3)


def _causal(report: Report) -> None:
    ids = causal.Ids()
    a = causal.Replica("a", ids=ids)
    b = causal.Replica("b", ids=ids)
    sent = a.send("b", "one")
    report.ok("a send advances the sender", a.state.text() == "a:1")
    report.ok("a message carries the sender's state", sent.deps.text() == "a:1")

    b.receive(sent)
    reply = b.send("a", "two")
    report.ok("the reply depends on what was received", reply.deps.get("a") == 1)
    report.ok("the reply also carries the sender's counter", reply.deps.get("b") == 1)

    late = causal.Replica("c", ids=ids)
    status = late.receive(reply)
    report.ok("a message with a missing dependency is held", status == "held")
    report.ok("a held message is remembered", len(late.held) == 1)
    report.ok("a held message is not delivered", not late.delivered)

    late.receive(sent)
    released = late.drain()
    report.ok(
        "the arrival of the dependency releases it",
        [message.id for message in released] == [reply.id],
    )
    report.ok(
        "released messages are delivered in order",
        [m.id for m in late.delivered] == [sent.id, reply.id],
    )
    report.ok("a gated delivery has no breaks", not causal.causality_violations(late.delivered))

    naive = causal.Replica("d", gated=False, ids=ids)
    naive.receive(reply)
    naive.receive(sent)
    broken = causal.causality_violations(naive.delivered)
    report.ok("an ungated delivery breaks causality", len(broken) == 1)
    report.ok("the break names the missing node", broken[0][1] == "a")
    report.ok("the break names what was needed", broken[0][2] == 1)
    report.ok("the break names what was had", broken[0][3] == 0)
    report.ok("the break prints as a line", causal.describe_violations(broken)[0].startswith("m"))
    report.ok("a clean order has no lines", not causal.describe_violations([]))

    report.refuses(
        "a message to itself is refused",
        causal.CausalError,
        lambda: causal.Message(1, "a", "a", VersionVector.empty(), "x"),
    )
    report.refuses(
        "a message id of zero is refused",
        causal.CausalError,
        lambda: causal.Message(0, "a", "b", VersionVector.empty(), "x"),
    )
    report.refuses("a replica needs a node name", causal.CausalError, lambda: causal.Replica(""))


def _pruning(report: Report) -> None:
    vectors = [
        VersionVector({"a": 4, "b": 2}),
        VersionVector({"a": 3, "b": 6}),
        VersionVector({"a": 5, "b": 2}),
    ]
    floor = prune.floor_of(vectors)
    report.ok("the floor is the pointwise minimum", floor.text() == "a:3,b:2")
    report.ok("a vector above the floor dominates it", prune.dominates_floor(vectors[0], floor))
    report.ok(
        "a vector below the floor does not",
        not prune.dominates_floor(VersionVector({"a": 1, "b": 2}), floor),
    )
    compacted = prune.compact(vectors[0], floor)
    report.ok("compaction drops the entries at the floor", compacted.text() == "a:4")
    report.ok("compaction never lowers a counter", compacted.get("a") == 4)

    above = [
        VersionVector({"a": 3, "b": 2, "c": 1}),
        VersionVector({"a": 4, "b": 2, "c": 1}),
        VersionVector({"a": 4, "b": 5, "c": 1}),
    ]
    measured = prune.measure(above, floor)
    report.ok("compaction changes nothing above the floor", measured.changed_above == 0)
    report.ok("the measurement counts the pairs", measured.above == 3)
    report.ok("a measurement with nothing below the floor holds", measured.held())

    mix = [*above, VersionVector({"a": 0, "b": 1, "c": 1})]
    broken = prune.measure(mix, floor)
    report.ok("compaction changes something below the floor", broken.changed_below > 0)
    report.ok("the broken examples are printed", bool(broken.examples_below))
    report.ok("the broken measurement still holds the claim", broken.held())
    relation, squeezed = prune.compacted_relation(above[0], above[2], floor)
    report.ok("the pair was comparable before", relation is Relation.BEFORE)
    report.ok("and stays comparable after", squeezed is Relation.BEFORE)

    report.refuses("an empty floor is refused", prune.PruneError, lambda: prune.floor_of([]))
    report.refuses(
        "an empty measurement is refused", prune.PruneError, lambda: prune.measure([], floor)
    )


def _command_line(report: Report) -> None:
    report.ok("the program has a name", bool(cli_module.PROGRAM))
    report.ok("the version is set", cli_module.VERSION == "0.1.0")

    code, out, _ = _quiet(lambda: cli_module.main(["compare", "--left", "a:1", "--right", "a:2"]))
    report.ok("a before pair exits zero", code == 0)
    report.ok("the comparison prints the relation", "before" in out)

    code, out, _ = _quiet(lambda: cli_module.main(["compare", "--left", "a:1", "--right", "b:1"]))
    report.ok("a concurrent pair exits one", code == cli_module.EXIT_CONCURRENT)
    report.ok("the concurrent line says so", "concurrent" in out)

    code, out, _ = _quiet(
        lambda: cli_module.main(["compare", "--left", "a:1", "--right", "b:1", "--json"])
    )
    report.ok("the json form parses", '"relation": "concurrent"' in out)

    code, out, _ = _quiet(lambda: cli_module.main(["merge", "--left", "a:1", "--right", "b:2"]))
    report.ok("a merge exits zero", code == 0)
    report.ok("the merge prints the join", "merged       a:1,b:2" in out)

    code, out, _ = _quiet(
        lambda: cli_module.main(["prune", "--vector", "a:3,b:2", "--floor", "a:3"])
    )
    report.ok("a sound compaction exits zero", code == 0)
    report.ok("pruning prints what is left", "compacted    b:2" in out)

    code, out, _ = _quiet(lambda: cli_module.main(["prune", "--vector", "a:1", "--floor", "a:3"]))
    report.ok("an unsound compaction exits one", code == cli_module.EXIT_CONCURRENT)
    report.ok("the unsound line says so", "sound        NO" in out)

    code, _, err = _quiet(lambda: cli_module.main(["compare", "--left", "a:x", "--right", "a:1"]))
    report.ok("an unreadable vector is a usage error", code == cli_module.EXIT_UNUSABLE)
    report.ok("the usage error names the problem", "whole number" in err)

    parsed = cli_module.build_parser().parse_args(["selftest"])
    report.ok(
        "the parser routes selftest without running it",
        parsed.handler is cli_module._command_selftest,
    )
    parsed = cli_module.build_parser().parse_args(["demo"])
    report.ok(
        "the parser routes demo without running it", parsed.handler is cli_module._command_demo
    )


def main() -> int:
    report = Report()
    _vectors(report)
    _lamport(report)
    _laws(report)
    _causal(report)
    _pruning(report)
    _command_line(report)
    for note in report.notes:
        print(note)
    print(f"selftest: {report.passed} checks passed, {report.failed} failed")
    return 0 if report.failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
