"""The rules, checked in-process, so `selftest` is a gate and not a demo.

Every check names the rule it defends. A red run points at a rule, not a line.
"""

from __future__ import annotations

import contextlib
import io
from pathlib import Path

from . import cli as cli_module
from .hashing import HashError, hex_of, leaf_hash, node_hash, sha256, unhex
from .naive import bare_root, duplicate_root, forgery
from .tree import EMPTY_ROOT, Proof, Tree, TreeError, depth, siblings_needed, split_point, verify

FIXTURES = Path(__file__).resolve().parent.parent.parent / "fixtures"
ENTRIES = FIXTURES / "entries.txt"
LEAVES = [f"entry-{number:02d}".encode() for number in range(1, 6)]
ROOT_FIVE = "d8fdb1f0c326081f8917ea62b5551153f7f2ad06edf53202861eb36afe8f360d"


class Report:
    """Counts passes and keeps the failures readable."""

    def __init__(self) -> None:
        self.passed = 0
        self.failed: list[str] = []

    def ok(self, name: str, condition: bool, detail: str = "") -> None:
        if condition:
            self.passed += 1
        else:
            self.failed.append(f"{name}: {detail}" if detail else name)

    def refuses(self, name: str, call, kind: type[Exception], needle: str) -> None:
        try:
            call()
        except kind as error:
            if needle in str(error):
                self.passed += 1
            else:
                self.failed.append(f"{name}: message was {str(error)!r}, wanted {needle!r}")
        except Exception as error:
            self.failed.append(f"{name}: raised {type(error).__name__}, wanted {kind.__name__}")
        else:
            self.failed.append(f"{name}: nothing was raised")


def _run(argv: list[str]) -> tuple[int, str]:
    """Run the CLI in-process, keep its stdout, and turn SystemExit into a code."""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(io.StringIO()):
        try:
            code = int(cli_module.main(argv))
        except SystemExit as exit_error:
            code = int(exit_error.code or 0)
    return code, buffer.getvalue()


def _hashing(report: Report) -> None:
    report.ok("a leaf is hashed with its own prefix", leaf_hash(b"a") == sha256(b"\x00a"))
    report.ok("a leaf is not hashed bare", leaf_hash(b"a") != sha256(b"a"))
    left, right = leaf_hash(b"a"), leaf_hash(b"b")
    report.ok("a node is hashed with its own prefix",
              node_hash(left, right) == sha256(b"\x01" + left + right))
    report.ok("a node keeps its order", node_hash(left, right) != node_hash(right, left))
    report.ok("a node digest is never a leaf digest",
              node_hash(left, right) != leaf_hash(left + right))
    report.refuses("node_hash refuses a short child",
                   lambda: node_hash(b"short", right), HashError, "32-byte children")
    report.ok("the leaf hash of entry-01 is the baked digest",
              hex_of(leaf_hash(b"entry-01"))
              == "5bc0582d78fe58e0b498dd7f39a86b652ce8827e67ad85ad9ea255ec848c2177")
    report.ok("hex round-trips", unhex(hex_of(left)) == left)
    report.refuses("unhex refuses a short digest",
                   lambda: unhex("ab"), HashError, "byte(s), not 32")
    report.refuses("unhex refuses a non-hex digest",
                   lambda: unhex("z" * 64), HashError, "not hexadecimal")


def _shape(report: Report) -> None:
    points = {2: 1, 3: 2, 4: 2, 5: 4, 6: 4, 7: 4, 8: 4, 9: 8, 16: 8, 17: 16}
    measured = {count: split_point(count) for count in points}
    report.ok("the split is the largest power of two below the count",
              measured == points, str(measured))
    report.refuses("a range of one cannot be split",
                   lambda: split_point(1), TreeError, "cannot be split")
    report.ok("depth is the bit length of size - 1",
              [depth(size) for size in (1, 2, 3, 4, 5, 8, 9)] == [0, 1, 2, 2, 3, 3, 4])
    measured_needs = [siblings_needed(index, 5) for index in range(5)]
    report.ok("the RFC shape is not level, so the count depends on the index",
              measured_needs == [3, 3, 3, 3, 1], str(measured_needs))
    report.ok("depth is the upper bound of the per-index count",
              all(siblings_needed(index, size) <= depth(size)
                  for size in range(1, 18) for index in range(size)))
    report.ok("the empty root is sha256 of nothing",
              Tree([]).root() == EMPTY_ROOT == sha256(b""))
    report.ok("the baked empty root is the known sha256 of the empty string",
              hex_of(EMPTY_ROOT)
              == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
    report.ok("a single leaf's root is its own hash",
              Tree([b"only"]).root() == leaf_hash(b"only"))
    report.ok("five leaves hash to the baked root", hex_of(Tree(LEAVES).root()) == ROOT_FIVE)
    report.ok("the root depends on the leaf order",
              Tree([b"a", b"b"]).root() != Tree([b"b", b"a"]).root())


def _proofs(report: Report) -> None:
    broken: list[str] = []
    for size in range(1, 18):
        leaves = [f"leaf-{number}".encode() for number in range(size)]
        built = Tree(leaves)
        for index in range(size):
            proof = built.prove(index)
            if len(proof.path) != siblings_needed(index, size):
                broken.append(f"size {size} index {index} carried {len(proof.path)} siblings")
                continue
            verdict = verify(index, leaves[index], proof.path, root=built.root(), size=size)
            if not verdict.ok:
                broken.append(f"size {size} index {index}: {verdict.reason}")
    report.ok("every honest proof verifies, sizes 1 to 17", not broken, "; ".join(broken[:3]))

    tree = Tree(LEAVES)
    proof = tree.prove(3)
    shifted = verify(4, LEAVES[3], proof.path, root=tree.root(), size=tree.size)
    report.ok("a proof moved to another index is refused", not shifted.ok, shifted.reason)

    changed = list(proof.path)
    changed[0] = leaf_hash(b"somebody else")
    forged = verify(3, LEAVES[3], tuple(changed), root=tree.root(), size=tree.size)
    report.ok("a changed sibling is refused", not forged.ok, forged.reason)

    report.ok("the proof carries the root it proves", proof.root == tree.root())
    report.ok("a proof round-trips through JSON", Proof.from_dict(proof.as_dict()) == proof)
    report.refuses("a payload that is not a proof is refused",
                   lambda: Proof.from_dict({"index": 0}), TreeError, "this is not a proof")

    out_of_range = verify(5, LEAVES[4], (), root=tree.root(), size=5)
    report.ok("index 5 of 5 is refused",
              not out_of_range.ok and "not in a tree" in out_of_range.reason,
              out_of_range.reason)
    short = verify(3, LEAVES[3], proof.path[:-1], root=tree.root(), size=5)
    report.ok("a short path is refused",
              not short.ok and "needs 3" in short.reason, short.reason)
    shallow = tree.prove(4)
    report.ok("the lone right leaf of a five-leaf tree needs one sibling",
              len(shallow.path) == 1 and siblings_needed(4, 5) == 1)
    shallow_ok = verify(4, LEAVES[4], shallow.path, root=tree.root(), size=5)
    report.ok("a one-sibling proof for index 4 still verifies", shallow_ok.ok,
              shallow_ok.reason)
    wide = verify(3, LEAVES[3], (b"x" * 31, *proof.path[1:]), root=tree.root(), size=5)
    report.ok("a 31-byte sibling is refused",
              not wide.ok and "not 32" in wide.reason, wide.reason)
    empty = verify(0, b"a", (), root=EMPTY_ROOT, size=0)
    report.ok("an empty tree has no leaf to prove",
              not empty.ok and "no leaf" in empty.reason, empty.reason)


def _wrong_trees(report: Report) -> None:
    numbers = forgery(LEAVES)
    report.ok("without a prefix the forged leaf has the two-leaf root",
              numbers["two_leaf_bare_root"] == numbers["forged_bare_root"])
    report.ok("with a prefix the same forgery fails",
              numbers["two_leaf_prefixed_root"] != numbers["forged_prefixed_root"])
    report.ok("the forgery is the 64 bytes of the two child digests",
              numbers["forged_leaf_bytes"] == 64)
    report.ok("the duplicate-the-odd tree disagrees with the RFC tree",
              duplicate_root(LEAVES) != Tree(LEAVES).root())
    report.ok("the duplicate root is the baked value",
              hex_of(duplicate_root(LEAVES))
              == "f8a8baf16827be866e7fbb3f6c725964ec7e663d4e95cf3dedfd3457b9801f74")
    report.ok("the bare tree is not the prefixed tree",
              hex_of(bare_root(LEAVES)) != hex_of(Tree(LEAVES).root()))
    report.ok("a one-leaf duplicate tree is just the leaf hash",
              duplicate_root([b"only"]) == leaf_hash(b"only"))
    report.ok("an empty duplicate tree is the empty root", duplicate_root([]) == EMPTY_ROOT)


def _command_line(report: Report) -> None:
    code, output = _run(["root", "--leaves", str(ENTRIES)])
    report.ok("root reads a fixture and exits 0", code == 0, output)
    report.ok("root prints the baked root", ROOT_FIVE in output, output)

    code, output = _run(["prove", "--leaves", str(ENTRIES), "--index", "3"])
    report.ok("prove exits 0", code == 0, output)
    report.ok("prove prints three siblings", "3 sibling(s)" in output, output)
    path = [line.split()[-1] for line in output.splitlines() if line.startswith("  ")]

    code, output = _run(["verify", "--leaf", "entry-04", "--index", "3", "--size", "5",
                         "--root", ROOT_FIVE, "--path", ",".join(path)])
    report.ok("verify accepts an honest proof", code == 0, output)
    report.ok("verify says it recomputed the root", "recomputes the root" in output, output)

    code, output = _run(["verify", "--leaf", "entry-05", "--index", "3", "--size", "5",
                         "--root", ROOT_FIVE, "--path", ",".join(path)])
    report.ok("verify refuses a changed leaf with exit 1", code == 1, output)

    code, output = _run(["verify", "--leaf", "entry-04", "--index", "3"])
    report.ok("verify without a path is a usage error", code == 2, output)

    code, output = _run(["root", "--leaves", "/nonexistent/leaves.txt"])
    report.ok("a missing leaf file is a usage error", code == 2, output)

    code, output = _run(["prove", "--leaves", str(ENTRIES), "--index", "9"])
    report.ok("an index past the end is a usage error", code == 2, output)

    code, output = _run(["--version"])
    report.ok("--version exits 0", code == 0, output)

    code, output = _run(["demo"])
    report.ok("demo exits 0", code == 0, output[-200:])
    report.ok("demo prints six stories", output.count("-> holds") == 6, output[-200:])


def main() -> int:
    report = Report()
    _hashing(report)
    _shape(report)
    _proofs(report)
    _wrong_trees(report)
    _command_line(report)
    for name in report.failed:
        print(f"  failed: {name}")
    if report.failed:
        print(f"selftest: {report.passed} passed, {len(report.failed)} failed")
        return 1
    print(f"selftest: {report.passed} checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
