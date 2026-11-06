# {{ title }}

{{ description }}

A Merkle proof says "this leaf is in this tree" without shipping the tree. That
claim is worth exactly as much as the two rules underneath it: how a leaf is
hashed, and how a tree splits. Get either wrong and the proof verifies for
documents that were never in the tree. So this stack keeps the rules small,
writes them down, and measures what the wrong versions cost.

```
{{ npm_name }} demo
```

## The rules this tree keeps

1. **A leaf is hashed with a `0x00` prefix, a node with `0x01`.** One hash
   function cannot tell a leaf from a node. Hash both the same way and
   `sha256(left || right)` is simultaneously a node's digest and the digest of a
   leaf whose content is those 64 bytes, so a one-leaf tree over that content has
   the same root as the two-leaf tree. The prefix makes the two inputs different.

2. **The root is `sha256` of nothing when there are no leaves.** A special case
   is a decision; leaving it undefined means two implementations disagree on the
   empty tree and nobody notices until a proof fails in production.

3. **The tree splits at the largest power of two below the leaf count** (the RFC
   6962 shape). For five leaves that is `H(H(H(a,b),H(c,d)), e)`. Bitcoin's rule
   duplicates the last node instead, giving `H(H(H(a,b),H(c,d)), H(e,e))`. Same
   leaves, different root, so **a proof is meaningless without the rule that
   produced it** - the root alone does not identify the algorithm.

4. **A proof carries one sibling per level, and the count depends on the
   index.** The RFC shape is not level: in a tree of five leaves index 3 needs
   three siblings and index 4 needs one, because the top split is `4 | 1`. The
   verifier derives the count from the index and the size and refuses any other
   number, so a padded or truncated proof is refused rather than folded.

5. **A proof is bound to its index.** The verifier folds the siblings in the
   order the index dictates; give it a sibling from another slot and the
   recomputed root disagrees. Siblings are stored **nearest-first**, and the fold
   runs **bottom-up**, so the decisions are recorded walking down and applied in
   reverse. Consuming the path from the top combines a half-folded hash with a
   sibling from the wrong level, and every honest proof is refused.

6. **A proof is bound to its size.** The size decides how many siblings the index
   may carry. Note the honest limit: for an index whose subtree shape matches
   (index 3 of five and of six leaves both need three siblings) the fold is the
   same, so the size cannot always be recovered from the proof. The verifier must
   be given the root **and** the size it belongs to, and the CLI refuses an
   `--index` that contradicts a `--proof` file for that reason.

7. **Every failure names the rule.** Out of range, wrong sibling length, wrong
   sibling count, wrong root: each has its own message, because "invalid proof"
   sends a user to read the whole tree.

## A real run

```
$ {{ npm_name }} demo
1. an inclusion proof recomputes the root
  leaves         5
  root           d8fdb1f0c326081f8917ea62b5551153…
  proving        index 3, the fourth leaf
  path           3 sibling(s), as many as this index needs
  index 4 needs  1 sibling(s): the shape is not level
  verdict        ok       the proof recomputes the root in 3 step(s)
  the verifier never sees the other four leaves, only their hashes
  -> holds

2. a changed leaf cannot produce the same root
  honest leaf    ok       the proof recomputes the root in 3 step(s)
  forged leaf    refused  the proof recomputes 2958f85fef7a5e1f… but the root is d8fdb1f0c326081f…
  recomputed     2958f85fef7a5e1f42d24b1e2bbca24f…
  the root       d8fdb1f0c326081f8917ea62b5551153…
  one changed byte changes every hash on the way up, so the mismatch is total
  -> holds

3. without a domain prefix, a node passes as a leaf
  two leaves     3aa48f4b474716bf76fb277925b42652… (unprefixed)
  one forged     3aa48f4b474716bf76fb277925b42652… (unprefixed)
  same root      True, without the prefix
  the forgery    64 bytes: the two child digests side by side
  same root      False, with the prefix
  a node's digest was a valid leaf digest, and now it is not
  -> holds

4. a proof belongs to one index of one tree
  as proved      ok       the proof recomputes the root in 3 step(s)
  as index 3     refused  the proof recomputes 197cca5e5e9a44ef… but the root is d8fdb1f0c326081f…
  as size 4      the proof carries 3 sibling(s) but index 2 of a tree of 4 needs 2
  as size 6      ok       the proof recomputes the root in 3 step(s) (6 has the depth of 5)
  the index decides the fold; the size only decides how many siblings there can be, so a size that shares the depth cannot be told apart
  -> holds

5. the empty and single-leaf trees still answer
  empty tree     e3b0c44298fc1c149afbf4c8996fb924… which is sha256 of nothing
  one leaf       root equals the leaf hash: True
  its proof      ok       the proof recomputes the root in 0 step(s)
  index 5 of 5   index 5 is not in a tree of 5 leaf/leaves
  short path     the proof carries 2 sibling(s) but index 2 of a tree of 5 needs 3
  the degenerate sizes are the ones a hand-written verifier forgets
  -> holds

6. the tree's shape is part of the root
  split at 4     d8fdb1f0c326081f8917ea62b5551153… (largest power of two below 5)
  duplicate odd  f8a8baf16827be866e7fbb3f6c725964… (the other rule)
  same root      False
  the proof      the proof recomputes d8fdb1f0c326081f… but the root is f8a8baf16827be86…
  the shape is part of the contract, so the rule has to be named
  -> holds
```

The CLI does the same work on your own files:

```
$ {{ npm_name }} root --leaves fixtures/entries.txt
size         5
root         d8fdb1f0c326081f8917ea62b5551153f7f2ad06edf53202861eb36afe8f360d
```

```
$ {{ npm_name }} prove --leaves fixtures/entries.txt --index 3
index        3 of 5
leaf         36ec2b842ce19ff8e2a7f484eec3ccf44e71cf59d458581ab9098e3e36ed8189
path         3 sibling(s)
  1. 3b1b1db30d87a51b6573b287df6b29be1a1dfe06ec4d6d1125604792fe3e9c9c
  2. c9bbfb234fe9e55ac28ae219060f76e79386bfad98ac36fc1ef25d086c5b565f
  3. f7e7bd4e314e13708b39187ce4b169492ae29ab78c4fa5b3835dd3986e62a526
root         d8fdb1f0c326081f8917ea62b5551153f7f2ad06edf53202861eb36afe8f360d
```

`prove --json` writes the same proof as a file, and `verify --proof` reads it
without ever seeing the other leaves. The last leaf of the same tree shows why
the sibling count is a property of the index, not of the size:

```
$ {{ npm_name }} prove --leaves fixtures/entries.txt --index 4
index        4 of 5
leaf         f7e7bd4e314e13708b39187ce4b169492ae29ab78c4fa5b3835dd3986e62a526
path         1 sibling(s)
  1. acc03204ccbb0d2dad1c6521aeecdcb7549c34c8e11280a60e6e424a05c023d8
root         d8fdb1f0c326081f8917ea62b5551153f7f2ad06edf53202861eb36afe8f360d
```

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | the command did what it said, or the proof verified |
| 1 | the proof was refused, or a demo story no longer holds |
| 2 | the arguments or the input file cannot describe a tree or a proof |

The distinction matters in a pipeline: `1` is a fact about the data, `2` is a
fact about your invocation. Retrying on `2` never helps, and treating `1` as a
crash hides a refused forgery.

## Layout

```
src/{{ package_name }}/hashing.py   prefixed leaf and node hashes, hex helpers
src/{{ package_name }}/tree.py      split rule, root, prove, verify
src/{{ package_name }}/naive.py     the unprefixed and duplicate-odd trees, for the demo only
src/{{ package_name }}/demo.py      six stories, each of which must hold
src/{{ package_name }}/cli.py       root / prove / verify / demo / selftest
src/{{ package_name }}/selftest.py  the rules as in-process checks
tests/                              pytest, including a brute-force sweep of sizes 1..24
fixtures/entries.txt                five leaves, so the numbers here are reproducible
```

## What this stack does not do

- **No consistency proofs.** Proving that today's tree extends yesterday's is a
  different (and equally interesting) proof.
- **No proof of absence.** A Merkle tree cannot show that a leaf is *not* there
  without an ordering rule; that is what a sparse Merkle tree or an accumulator
  is for.
- **No storage layer.** Leaves are hashed in memory; a 10-million-leaf tree wants
  a store and a cache in front of the same rules.
- **No signature.** A root is a digest, not an attestation: who published it is
  somebody else's problem (see `python-url-signing` for the signing half).

## Verify it

```
uv venv && uv pip install -e . pytest ruff
.venv/bin/ruff check .
.venv/bin/python -m pytest
.venv/bin/python -m {{ package_name }} selftest
PY=.venv/bin/python bash smoke.sh
```
