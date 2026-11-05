# {{ title }}

{{ description }}

A tiny, dependency-free evaluation harness: gold answers in JSONL, predictions in
JSONL, one score out — plus a record of the run you can diff against the last one.

## Why a harness and not a script

Three rules are baked in, because each one is a way published numbers go wrong:

* **A missing prediction scores zero.** Dropping unanswered examples makes a model
  that answered 3 of 100 questions look perfect on the ones it answered. The report
  lists the missing ids instead of quietly shrinking the denominator.
* **The metric is named in the output and in the record.** `token_f1` and
  `exact_match` disagree on almost everything; a score without its metric is not
  comparable to anything.
* **Every record carries provenance** — the git commit (with `+dirty` when the tree
  was not clean), the timestamp, and the per-example scores.

## Run

```console
$ {{ npm_name }} run --data data/dev.jsonl --predictions data/predictions.good.jsonl --out runs/good.json
metric    token_f1
score     0.9167
answered  4/4
record    runs/good.json
```

`--predictions -` reads the prediction rows from stdin, so a model can pipe them in.
`--metric` picks `exact_match`, `token_f1` (default) or `contains`.

## Compare two runs

```console
$ {{ npm_name }} compare --baseline runs/good.json --candidate runs/bad.json
delta     -0.6959
regressed 4
```

`compare` exits 1 when any example got worse and 0 when nothing did, which is what
makes it usable as a CI gate: `--tolerance 0.01` lets a 1e-2 drop through.

## Files

```console
$ cat data/dev.jsonl
{"id": "cap-1", "prompt": "What is the capital of France?", "gold": "Paris"}

$ cat data/predictions.good.jsonl
{"id": "cap-1", "prediction": "Paris."}
```

Text before scoring is lowercased, stripped of punctuation, and whitespace-collapsed,
so `"Paris."` and `"paris"` are the same answer. `token_f1` compares token multisets,
so repeating a word cannot farm recall.

## Test

```console
$ pytest
$ bash smoke.sh
```
