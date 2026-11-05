# {{ title }}

Batch inference that survives being interrupted.

Send one JSONL line per prompt to any OpenAI-compatible `/chat/completions`
endpoint, get one JSONL line per answer back, and rerun the command whenever you
like: ids already present in the results file are skipped, not sent again.

```bash
uv venv --quiet && uv pip install --python .venv/bin/python -e .
.venv/bin/python -m {{ package_name }} run \
  --requests data/requests.jsonl \
  --out results.jsonl \
  --base-url http://127.0.0.1:5468/v1
```

## Why it is shaped like this

- **A failure is a record, not an exception.** `ok: false` with the reason goes
  into the same file as the answers, so a run of 10 000 prompts does not lose its
  first 9 000 because prompt 9 001 met a 400.
- **The results file is the checkpoint.** It is append-only and flushed per line,
  so a kill -9 costs at most the one request in flight. A torn final line is
  discarded on the next run rather than turning into a parse error.
- **Retry only what can succeed.** 408/429/5xx and network errors back off
  exponentially (`--backoff`, doubled per attempt, `--max-attempts` total).
  Any other 4xx fails on the first attempt: retrying a malformed request only
  spends quota.
- **Exit codes are the contract.** `0` everything answered, `1` something failed
  permanently (the answers are still on disk), `2` the batch itself is unusable —
  missing, not JSONL, duplicate ids, or the output cannot be opened.

## Request and result lines

```json
{"id": "cap-1", "prompt": "Say hello"}
{"attempts": 1, "error": "", "id": "cap-1", "model": "stub-model", "ok": true,
 "output": "echo: Say hello", "tokens_in": 2, "tokens_out": 1}
```

`attempts` is how many tries the answer took, so a retry is visible in the data
instead of hidden in a log. Use `--requests -` to read the batch from stdin:
`--out` is still where the answers go.

## Offline tests

`tests/stub.py` is a real HTTP server that speaks the same API and misbehaves on
demand (`FAIL429` answers 429 twice, `FAIL400` answers 400 forever), so the retry
and failure paths are proven against a socket and the suite needs no network.

```bash
.venv/bin/python -m pytest
.venv/bin/python -m {{ package_name }} selftest
PY=.venv/bin/python bash smoke.sh
```
