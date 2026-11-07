"""The invariants, runnable in a fresh checkout: the tree proves itself.

Every claim here is computed at run time against the real modules. The
checker's own promises come first — it is shipped and tested here, not
assumed — then the gate, the walk, the storm, and the edges.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import check, corpus, node
from .corpus import Snapshot
from .keys import MAX_KEY, ensure_key
from .node import Node
from .tree import RBTree, TreeError
from .workload import rebuild_matches, run_storm

FIXTURE = "a red node never fathers a red node"


@dataclass
class Report:
    """Every check the tree answered, and the ones it broke."""

    checks: int = 0
    failed: int = 0
    lines: list[str] = field(default_factory=list)

    def section(self, name: str) -> None:
        self.lines.append(f"[{name}]")

    def ok(self, claim: str, held: bool) -> None:
        self.checks += 1
        if not held:
            self.failed += 1
            self.lines.append(f"  FAIL {claim}")

    def equal(self, claim: str, found: object, expected: object) -> None:
        self.checks += 1
        if found != expected:
            self.failed += 1
            self.lines.append(f"  FAIL {claim}: {found!r} != {expected!r}")

    def refuses(self, claim: str, call, error: type[Exception]) -> None:
        self.checks += 1
        try:
            call()
        except error:
            return
        except Exception as stray:
            self.failed += 1
            self.lines.append(f"  FAIL {claim}: raised {stray!r}")
            return
        self.failed += 1
        self.lines.append(f"  FAIL {claim}: nothing refused")

    def render(self) -> str:
        body = "\n".join(self.lines)
        tail = f"selftest: {self.checks - self.failed} checks passed, " \
            f"{self.failed} failed"
        return f"{body}\n{tail}" if body else tail


def _gate(report: Report) -> None:
    report.section("gate")
    report.equal("an integer passes the gate", ensure_key(7), 7)
    report.equal("the edge is a key", ensure_key(MAX_KEY), MAX_KEY)
    report.refuses("a float is refused", lambda: ensure_key(1.5), ValueError)
    report.refuses("a bool is refused", lambda: ensure_key(True), ValueError)
    report.refuses("past the edge is refused",
                   lambda: ensure_key(MAX_KEY + 1), ValueError)


def _checker(report: Report) -> None:
    report.section("checker")
    report.ok("the checker ships the promise in its docstring",
              FIXTURE in " ".join((check.__doc__ or "").split()))
    report.ok("nothing stands red", not check.is_red(None))
    single = node.blacken(node.leaf(5))
    report.ok("a lone black node holds", check.holds(single))
    report.equal("a lone black node counts one",
                 check.black_height(single), 1)
    report.equal("an empty tree counts zero", check.black_height(None), 0)
    report.ok("the checker names a red root",
              any("red" in word for word in
                  check.problems(Node(4, check.RED))))
    report.ok("the checker names a red father",
              any("fathers" in word for word in
                  check.problems(Node(5, check.BLACK,
                                      Node(3, check.RED, Node(2))))))
    split = Node(5, check.BLACK, Node(3, check.BLACK), None)
    report.ok("the checker names a height split",
              any("split" in word for word in check.problems(split)))
    crooked = Node(5, check.BLACK, Node(3), Node(7, check.RED, Node(4)))
    report.ok("the checker names an out-of-order key",
              any("ceiling" in word or "floor" in word
                  for word in check.problems(crooked)))


def _walk(report: Report) -> None:
    report.section("walk")
    corpus_keys = corpus.synthetic(120, seed=5, span=150)
    tree = RBTree(corpus_keys)
    report.equal("the walk is the sorted list",
                 tree.keys(), sorted(set(corpus_keys)))
    report.equal("the walk answers the count", tree.count(),
                 len(set(corpus_keys)))
    report.ok("the checker names nothing", tree.invariant())
    report.equal("the edges answer equal", check.edge_heights(
        tree._root)[0], check.edge_heights(tree._root)[1])
    report.ok("membership answers a set",
              all(tree.has(key) is (key in set(corpus_keys))
                  for key in [*corpus_keys[:8], MAX_KEY, 0]))


def _removals(report: Report) -> None:
    report.section("removals")
    tree = RBTree([4, 2, 9, 1, 3, 8, 11])
    report.equal("remove of an absent key refuses",
                 _raises(tree, 77), "TreeError")
    tree.remove(9)
    report.equal("a removal leaves the walk sorted",
                 tree.keys(), [1, 2, 3, 4, 8, 11])
    report.ok("the shape holds after removal", tree.invariant())
    smallest = tree.drop_min()
    report.equal("drop_min hands back the smallest", smallest, 1)
    report.equal("drop_min leaves the walk sorted",
                 tree.keys(), [2, 3, 4, 8, 11])
    report.ok("the shape holds after drop_min", tree.invariant())
    while len(tree):
        tree.drop_min()
    report.equal("the tree empties in order", tree.keys(), [])
    report.ok("an empty tree still holds", tree.invariant())
    report.refuses("drop_min of an empty tree refuses",
                   tree.drop_min, TreeError)


def _raises(tree: RBTree, key: int) -> str:
    try:
        tree.remove(key)
    except TreeError:
        return "TreeError"
    return "silent"


def _storm(report: Report) -> None:
    report.section("storm")
    storm = run_storm(seed=23)
    report.equal("the storm breaks nothing", storm.breaks, 0)
    report.ok("the storm ends seated", storm.seated)
    report.ok("a rebuild answers identically",
              rebuild_matches(corpus.synthetic(50, seed=8, span=90)))


def _stories(report: Report) -> None:
    report.section("stories")
    from .demo import stories

    for story in stories():
        report.ok(f"story: {story.title}", story.held)
    snapshot = Snapshot((1, 2, 3), 7)
    report.equal("a snapshot round-trips",
                 Snapshot.loads(snapshot.dumps()), snapshot)
    report.refuses("half a snapshot refuses",
                   lambda: Snapshot.loads('{"keys": [1]}'), ValueError)


def run() -> Report:
    """Every section, computed against the shipped modules."""
    report = Report()
    _gate(report)
    _checker(report)
    _walk(report)
    _removals(report)
    _storm(report)
    _stories(report)
    return report
