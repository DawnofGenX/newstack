# {{ title }}

{{ description }}

A saga is a sequence of local transactions, each with a compensating action,
because there is no distributed transaction to roll back. This project is a
runner for that idea plus the journal that makes it survivable: every step is
appended to a JSONL file with `fsync` *before* its outcome is known, so a
process that dies mid-saga leaves evidence instead of a mystery.

## The rules this runner keeps

1. **Compensations run in reverse.** A dependency is never torn down before the
   thing that depends on it.
2. **The failing step is not compensated.** It reported failure; compensating it
   would claim an effect that was never admitted to. Whatever partial work it
   did is its own business, and it must be safe to call twice under the same
   idempotency key.
3. **One broken compensation does not excuse the others.** If the refund
   endpoint is down, the hotel still gets released -- and the saga ends
   `incomplete`, not "rolled back".
4. **Irreversible steps are named.** A step with no compensation that already
   succeeded makes the rollback `incomplete`, with the step listed. Pretending
   an email was unsent is the most expensive lie this code could tell.
5. **Re-running is a no-op.** A completed or already-unwound saga is answered
   from the journal; the steps are not re-executed.
6. **An interrupted step is retried, not assumed.** `step.started` with no
   outcome means the process died mid-call, so the runner re-runs it with the
   *same* idempotency key and records `step.retried`.
7. **A torn final line is not history.** The reader drops a half-written last
   line (the writer died mid-append) but refuses a torn line in the middle,
   because that means records were lost and guessing which ones invents history.

## Quick start

```sh
uv venv --allow-existing .venv
uv pip install --python .venv/bin/python -e . pytest ruff
.venv/bin/python -m {{ package_name }} demo
```

The demo runs four scenarios in a temporary directory: everything works, the
flight is declined, the refund endpoint is down, and the refund fails once then
works.

```sh
.venv/bin/python -m {{ package_name }} run --journal saga.jsonl
.venv/bin/python -m {{ package_name }} run --journal saga.jsonl --break-compensation charge-card
.venv/bin/python -m {{ package_name }} journal --journal saga.jsonl
```

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | completed |
| 1 | rolled back cleanly |
| 2 | rollback incomplete: something the saga did is still true |
| 3 | the tool could not read its journal or arguments |

Exit code 2 is the one to page on. It is not "mostly fine": it means the saga
left the world in a state nobody planned.

## Using the runner

```python
from {{ package_name }}.runner import Step, Saga

def charge(context):
    # context.key is stable across retries and restarts: pass it to the provider
    return payments.charge(context.key, amount=42)

def refund(context):
    payments.refund(context.key)

saga = Saga(
    "book-trip",
    [
        Step("reserve-hotel", reserve, release),
        Step("charge-card", charge, refund, max_attempts=2, retry_on=(TimeoutError,)),
        Step("book-flight", book, cancel),
    ],
    "saga.jsonl",
)
outcome = saga.run()
if outcome.status != "completed":
    print("\n".join(outcome.lines()))
```

`max_attempts` applies to the compensation too: a refund that times out once and
works on the second attempt leaves a `compensation_failed` record for the first
attempt and a `compensated` record for the second.

## What is in the box

| path | what it is |
| ---- | ---------- |
| `src/{{ package_name }}/journal.py` | append-only JSONL reader/writer, torn-line rules |
| `src/{{ package_name }}/runner.py` | `Step`, `Context`, `Saga`, `Outcome` |
| `src/{{ package_name }}/demo.py` | the booking saga with failure knobs |
| `src/{{ package_name }}/cli.py` | `run`, `journal`, `demo`, `selftest` |
| `tests/` | journal, runner, resume and CLI behaviour |

No runtime dependencies: the journal is `json` plus `os.fsync`, and the runner is
the standard library.

## Licence

MIT. See LICENSE.
