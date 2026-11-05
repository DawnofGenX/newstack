# {{ title }}

Retrieval numbers that survive review: chunk the corpus, rank with BM25, and score
against judgements you can defend. No API keys, no model downloads, no network — the
same corpus and the same judgements always produce the same report.

## Quick start

```bash
uv venv && uv pip install --python .venv/bin/python -e . pytest ruff
.venv/bin/python -m {{ package_name }} eval
.venv/bin/python -m {{ package_name }} search "how do I rotate a signing key"
PY=.venv/bin/python bash smoke.sh
```

```
$ .venv/bin/python -m {{ package_name }} eval
report 6 queries, 5 judged, 1 skipped
chunks 26 (size 40, overlap 10)
skip   no judgements   a query nothing answers
recall@3 1.00  ndcg 1.00  rr 1.00  rotate-key.md  how do I rotate a signing key
recall@3 1.00  ndcg 1.00  rr 1.00  shard-rebalancing.md  rebalance shards after a node failure
recall@3 0.50  ndcg 0.83  rr 1.00  quota-limits.md  request limit per tenant
recall@3 0.50  ndcg 0.83  rr 1.00  retry-policy.md  what happens when a write is retried
recall@3 1.00  ndcg 1.00  rr 1.00  cold-start.md  which request is slow during a rolling deploy
macro  recall@3 0.80  precision 0.28  ndcg 0.78  mrr 0.83
micro  recall@3 0.71
```

## The commands

| Command | What it answers |
| --- | --- |
| `eval` | every judged query, scored; `--json` for a file you can diff |
| `search QUERY --k N` | which chunks won, and by how much |
| `compare --baseline A --candidate B` | did this change make retrieval worse? exits 1 if so |
| `selftest` | do the metrics still mean what they claim? |

Exit codes: `0` fine, `1` regression or a query that matched nothing, `2` unusable
input (missing corpus, malformed judgements, a judgement for a document that is not in
the corpus).

## The seven ways a retrieval report lies

1. **Counting chunk hits as document hits.** Three chunks of one document are one
   result, not three. `ranked_documents()` collapses them before any metric runs.
2. **Dividing precision by the number of results returned.** A query with one result
   then scores 1.0. Precision divides by `k`.
3. **A denominator that shrinks.** A missing prediction must score zero, never be
   dropped from the average. Unjudged queries are reported as `skipped`, never averaged
   in as if they had succeeded.
4. **Treating unjudged documents as irrelevant.** With `ndcg`, an unjudged document in
   the top slot is a wasted slot — it earns no gain. Judgements must cover what the
   system actually returns, or the number is fiction.
5. **Reporting macro or micro alone.** Macro is per-query fairness; micro is pooled
   coverage and is dominated by queries with many relevant documents. Both are printed.
6. **A window size nobody recorded.** Chunk size decides what is even findable, so
   `size`, `overlap`, `k` and the chunk count go into the report and into `--json`.
7. **A benchmark that cannot fail.** `compare` gates macro recall, micro recall, ndcg
   and mrr; in CI the candidate report is compared against a committed baseline, so a
   regression fails the build instead of being noticed later.

## Layout

```
fixtures/corpus/*.md   five short documents about running a service
fixtures/qrels.json    queries, k, and graded judgements; one query is deliberately unjudged
src/{{ package_name }}/chunk.py      word windows with overlap, and a coverage check
src/{{ package_name }}/index.py      BM25 with a strictly positive idf
src/{{ package_name }}/metrics.py    recall, precision, rr, ndcg, mean-with-skip-count
src/{{ package_name }}/evaluate.py   the report (and macro vs micro)
src/{{ package_name }}/selftest.py   the checks that keep the numbers honest
```
