"""Six stories about what a proof actually proves.

Everything here is computed from the package itself, so a change that breaks a
rule turns the story into `-> BROKEN` instead of leaving a stale paragraph in the
README.
"""

from __future__ import annotations

from dataclasses import dataclass

from .hashing import hex_of, leaf_hash
from .naive import duplicate_root, forgery
from .tree import EMPTY_ROOT, Tree, siblings_needed, verify

LEAVES = [f"entry-{number:02d}".encode() for number in range(1, 6)]


@dataclass(frozen=True)
class Story:
    title: str
    lines: tuple[str, ...]
    held: bool


def _example() -> Tree:
    return Tree(LEAVES)


def inclusion_story() -> Story:
    tree = _example()
    proof = tree.prove(3)
    verdict = verify(proof.index, LEAVES[3], proof.path, root=tree.root(), size=tree.size)
    lines = (
        f"leaves         {tree.size}",
        f"root           {hex_of(tree.root())[:32]}…",
        "proving        index 3, the fourth leaf",
        f"path           {len(proof.path)} sibling(s), as many as this index needs",
        f"index 4 needs  {siblings_needed(4, tree.size)} sibling(s): the shape is not level",
        f"verdict        {verdict.line()}",
        "the verifier never sees the other four leaves, only their hashes",
    )
    return Story("1. an inclusion proof recomputes the root", lines,
                 verdict.ok and len(proof.path) == siblings_needed(3, 5))


def tampered_story() -> Story:
    tree = _example()
    proof = tree.prove(2)
    honest = verify(2, LEAVES[2], proof.path, root=tree.root(), size=tree.size)
    forged = verify(2, b"entry-03-forged", proof.path, root=tree.root(), size=tree.size)
    lines = (
        f"honest leaf    {honest.line()}",
        f"forged leaf    {forged.line()}",
        f"recomputed     {hex_of(forged.recomputed)[:32]}…",
        f"the root       {hex_of(tree.root())[:32]}…",
        "one changed byte changes every hash on the way up, so the mismatch is total",
    )
    return Story("2. a changed leaf cannot produce the same root", lines,
                 honest.ok and not forged.ok)


def forgery_story() -> Story:
    numbers = forgery(LEAVES)
    bare_equal = numbers["two_leaf_bare_root"] == numbers["forged_bare_root"]
    prefixed_equal = numbers["two_leaf_prefixed_root"] == numbers["forged_prefixed_root"]
    lines = (
        f"two leaves     {hex_of(numbers['two_leaf_bare_root'])[:32]}… (unprefixed)",
        f"one forged     {hex_of(numbers['forged_bare_root'])[:32]}… (unprefixed)",
        f"same root      {bare_equal}, without the prefix",
        f"the forgery    {numbers['forged_leaf_bytes']} bytes: the two child digests side by side",
        f"same root      {prefixed_equal}, with the prefix",
        "a node's digest was a valid leaf digest, and now it is not",
    )
    return Story("3. without a domain prefix, a node passes as a leaf", lines,
                 bare_equal and not prefixed_equal)


def index_story() -> Story:
    tree = _example()
    proof = tree.prove(2)
    right = verify(2, LEAVES[2], proof.path, root=tree.root(), size=tree.size)
    wrong_index = verify(3, LEAVES[2], proof.path, root=tree.root(), size=tree.size)
    smaller = verify(2, LEAVES[2], proof.path, root=tree.root(), size=4)
    same_depth = verify(2, LEAVES[2], proof.path, root=tree.root(), size=6)
    lines = (
        f"as proved      {right.line()}",
        f"as index 3     {wrong_index.line()}",
        f"as size 4      {smaller.reason}",
        f"as size 6      {same_depth.line()} (6 has the depth of 5)",
        "the index decides the fold; the size only decides how many siblings there can be, "
        "so a size that shares the depth cannot be told apart",
    )
    return Story("4. a proof belongs to one index of one tree", lines,
                 right.ok and not wrong_index.ok and not smaller.ok)


def edge_story() -> Story:
    empty_root = EMPTY_ROOT
    single = Tree([b"only"])
    proof = single.prove(0)
    single_verdict = verify(0, b"only", proof.path, root=single.root(), size=1)
    same_as_leaf = hex_of(single.root()) == hex_of(leaf_hash(b"only"))
    out_of_range = verify(5, LEAVES[4], (), root=single.root(), size=5)
    short = verify(2, LEAVES[2], _example().prove(2).path[:-1],
                   root=_example().root(), size=5)
    lines = (
        f"empty tree     {hex_of(empty_root)[:32]}… which is sha256 of nothing",
        f"one leaf       root equals the leaf hash: {same_as_leaf}",
        f"its proof      {single_verdict.line()}",
        f"index 5 of 5   {out_of_range.reason}",
        f"short path     {short.reason}",
        "the degenerate sizes are the ones a hand-written verifier forgets",
    )
    return Story("5. the empty and single-leaf trees still answer", lines,
                 single_verdict.ok and not out_of_range.ok and not short.ok)


def shape_story() -> Story:
    tree = _example()
    proof = tree.prove(3)
    rfc_root = tree.root()
    other_root = duplicate_root(LEAVES)
    mismatched = verify(3, LEAVES[3], proof.path, root=other_root, size=5)
    lines = (
        f"split at 4     {hex_of(rfc_root)[:32]}… (largest power of two below 5)",
        f"duplicate odd  {hex_of(other_root)[:32]}… (the other rule)",
        f"same root      {rfc_root == other_root}",
        f"the proof      {mismatched.reason}",
        "the shape is part of the contract, so the rule has to be named",
    )
    return Story("6. the tree's shape is part of the root", lines,
                 rfc_root != other_root and not mismatched.ok)


def stories() -> list[Story]:
    return [
        inclusion_story(),
        tampered_story(),
        forgery_story(),
        index_story(),
        edge_story(),
        shape_story(),
    ]


def render_stories() -> str:
    blocks: list[str] = []
    for story in stories():
        blocks.append(story.title)
        blocks.extend(f"  {line}" for line in story.lines)
        blocks.append("  -> holds" if story.held else "  -> BROKEN")
        blocks.append("")
    return "\n".join(blocks) + "\n"
