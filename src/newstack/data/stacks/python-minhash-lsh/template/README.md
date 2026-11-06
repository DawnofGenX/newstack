# {{ title }}

{{ description }}

Near-duplicate detection is two decisions and one measurement: what counts as the
same document (the shingle set), what counts as close enough (the threshold), and
how many true pairs the second decision actually finds (the recall). This stack
keeps all three visible, on a corpus it plants duplicates in, so every number in
the output is a number it computed.

## The rules this stack keeps

1. **The shingle set is the definition of similar; the hash only speeds it up.**
   Unimportant words and shingle size decide whether two documents are the same.
   The signature is a sketch of that set, never a second definition.

2. **A signature estimates the similarity, it does not measure it.** Every position
   agrees with probability equal to the Jaccard similarity, so the estimate is one
   draw with a standard deviation of `1/sqrt(width)`. The estimate is printed with
   that deviation, not instead of it.

3. **Banding is a decision about which false negatives you accept.** `bands * rows`
   positions give an S-curve: a pair at similarity `s` becomes a candidate with
   probability `1-(1-s**rows)**bands`. The half-way similarity is
   `(1-0.5**(1/bands))**(1/rows)` - the point where half the true pairs survive.

4. **A candidate is not a duplicate.** The banding proposes pairs and the estimate
   verifies them. Both counts are reported, so a rejected candidate is visible
   rather than silent.

5. **The filter may be wrong in one direction only.** A missing candidate is a
   missed duplicate, and the demo counts every one of them against the exact truth.
   There is no such thing as a false positive that reached the output.

6. **Recall is chosen before the data.** The curve can be printed without a corpus,
   and the demo then measures recall against that printed prediction - they agree to
   within a few points on every banding it tries.

7. **Width buys certainty about the estimate, not recall.** Changing the signature
   width changes how close the estimate lands; changing `bands` and `rows` changes
   which pairs you find. The two are independent and are reported separately.

## The demo

`python -m {{ package_name }} demo` runs six stories; each ends in `-> holds` or
`-> BROKEN`, and a broken story exits non-zero. Real output:

```
1. a signature estimates the similarity, it does not measure it
  pair         pair-20, two documents whose exact jaccard is 0.6198
  width    32   estimate 0.6875, promised deviation 0.1768
  width   128   estimate 0.6016, promised deviation 0.0884
  width   512   estimate 0.6094, promised deviation 0.0442
  width  2048   estimate 0.6128, promised deviation 0.0221
  the estimate is one draw from that error, not the similarity itself
  -> holds
```

```
3. banding turns a signature into a threshold you chose
  chosen       8 band(s) of 16 row(s), 128 positions for a 0.80 threshold, whose half-way similarity is 0.856
  similarity       4x32       8x16       32x4
        0.40      0.000      0.000      0.564
        0.60      0.000      0.002      0.988
        0.70      0.000      0.026      1.000
        0.80      0.003      0.204      1.000
        0.90      0.130      0.806      1.000
  a banding is a decision about which false negatives you accept
  -> holds
```

```
4. candidates are a fraction of the pairs, and they are verified
  documents    200, which is 19,900 pairs to compare
  banding      8 band(s) of 16 row(s), 128 positions
  candidates   77 pair(s), so 99.6% of the pairs are never compared
  exact        160 pair(s) at or above 0.80
  found        77 of 160, so 83 duplicate(s) never became a candidate at this banding
  refused      0 candidate(s) were rejected by the estimate, which is why a verified candidate is a decision and not a guess
  the filter is allowed to be wrong in one direction: a missing candidate is a missed duplicate
  -> holds
```

```
5. the recall you get is the curve you chose
  banding        predicted   measured   missed
  32 band(s) of 4 row(s), 128 positions   1.000      0.975        4
  16 band(s) of 8 row(s), 128 positions   0.995      0.975        4
  8 band(s) of 16 row(s), 128 positions   0.487      0.481       83
  4 band(s) of 32 row(s), 128 positions   0.025      0.013      158
  the measured recall tracks the curve, which is why the curve can be printed before the data
  -> holds
```

```
6. width buys certainty about the estimate, not recall
  width    rmse of the estimate   sqrt(s(1-s)/width)   pairs
    128                 0.0284               0.0312     160
    512                 0.0136               0.0156     160
   2048                 0.0064               0.0078     160
  a wider signature does not change the banding; it changes how much the estimate is worth
  -> holds
```

## Commands

```
$ {{ npm_name }} similar --left a.txt --right b.txt
shingles     13 and 13 at 5 word(s)
exact        jaccard 1.0000
estimate     1.0000 from 128 positions (deviation 0.0884)
threshold    0.80: similar
```

```
$ {{ npm_name }} candidates --corpus fixtures/corpus.jsonl
documents    6 (15 possible pairs)
banding      8 band(s) of 16 row(s), 128 positions, width 128
candidates   1 pair(s), 93.3% of the space never compared
exact        1 pair(s) at or above 0.80
found        1 of 1, recall 100.0%
verified     1 candidate(s) survive the estimate, 0 do not
precision    100.0%
```

```
$ {{ npm_name }} dedupe --corpus fixtures/corpus.jsonl --threshold 0.8
documents    6
candidates   1
joined       1 pair(s), 0 refused by the estimate
clusters     5 (1 duplicate(s) folded in)
   4. report-2024-q3, report-2024-q3-copy
```

```
$ {{ npm_name }} curve --width 128 --threshold 0.8
banding      8 band(s) of 16 row(s), 128 positions
half-way     similarity 0.856
similarity   probability
      0.00        0.0000
```

`signature --text FILE --width N [--json]` prints one document's signature, and
`signature --string TEXT` works without a file. Every command that reads a corpus
takes JSONL with one object per line, `{"name": "...", "text": "..."}`.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | the command answered the question |
| 1 | `similar` fell below the threshold, or `dedupe --fail-on-duplicates` found a duplicate |
| 2 | the request could not be answered: missing file, malformed corpus, banding wider than the signature |

## Layout

```
src/{{ package_name }}/
  shingles.py   normalization, the shingle set, exact Jaccard
  rng.py        SplitMix64, so the corpus is identical on every machine
  minhash.py    permutations, signatures, the estimate and its deviation
  lsh.py        banding, the S-curve, candidate pairs, pick()
  dedupe.py     union-find over verified candidate pairs
  measure.py    recall, precision, candidate reduction, estimate spread
  corpus.py     planted near-duplicates with a chosen similarity
  demo.py       the six stories
  cli.py        the command line
  selftest.py   the rules as checks
tests/          pytest: shingles, signatures, banding, clustering, measurement, CLI
fixtures/corpus.jsonl   six documents, one of them a near-copy
```

## Running it

```
uv venv && uv pip install -e . pytest ruff
.venv/bin/python -m {{ package_name }} demo
.venv/bin/pytest -q
PY=.venv/bin/python bash smoke.sh
```

## What this stack does not do

- It does not store signatures or bands in a database. `candidates` holds them in
  memory; a real system would shard the band keys.
- It does not handle near-duplicates across languages beyond lower-casing and
  word splitting, which is a decision about Unicode the caller has to make.
- It does not pick a threshold for you. `pick()` chooses a banding for a threshold
  you name, because the threshold is a product decision, not a statistical one.
