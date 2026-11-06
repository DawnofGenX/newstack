# Linearizability Checker

A register history is a record of what clients saw: each operation carries the
value it wrote or returned and the instants it was invoked and answered. The
history is **linearizable** when some single order of those operations agrees
with three things at once — the order each client's own program demands, the
real-time order (an operation that answered before another was invoked must
come first), and the values the reads returned.

This package decides that question instead of sampling it. When the answer is
yes it prints a witness order; when the answer is no it prints a **core** — the
smallest set of operations that is still refused, so the bug report is a
reproduction instead of a log.

```console
$ uv sync
$ uv run linearize check --history fixtures/sequential.jsonl
verdict    linearizable
reason     a witness order of 3 operation(s) exists
search     3 node(s), 0 memo hit(s), 3 operation(s)
witness    one order that holds:
  1  client 0 write 5 [0, 2)
  2  client 0 read 5 [3, 4)
  3  client 0 write 7 [5, 6)
```

The instant bracket `[invoked, answered)` is the whole input: an operation that
overlaps another may be ordered either way, an operation that finished before
another started may not.

## Rules this checker follows

1. **A witness is a proof, and it is checked like one.** The printed order is
   replayed value by value; a witness that does not reproduce every read is a
   bug in the checker, not a success. The selftest asserts the replay.

2. **A refusal must come with a core.** `shrink` drops operations one at a time
   while the rest stays refused. A refusal that cannot be narrowed is a refusal
   with a reason, not a verdict you have to take on trust:

   ```console
   $ uv run linearize check --history fixtures/stale-read.jsonl
   verdict    not linearizable
   reason     no order of the 2 operation(s) agrees with the per-client order, the real-time order and the values the reads returned
   search     2 node(s), 0 memo hit(s), 2 operation(s)
   core       1 of 2 operation(s), and removing any one of them makes the rest linearizable
     client 1 read 3 [3, 4)
   $ echo $?
   1
   ```

   Here the core is the read alone: `3` was never written and the register
   started at `0`, so no write is needed to make the history impossible.

3. **Only real-time order prunes the search.** An operation may be linearized
   next when no unlinearized operation answered before it was invoked. That is
   the only rule applied — the checker never guesses that a later write wins
   because it is later.

4. **The pruning is measured, not asserted.** `compare` runs the same history
   through the search and through an exhaustive permutation yardstick and
   insists the two verdicts and witnesses agree:

   ```console
   $ uv run linearize compare --history fixtures/straddle.jsonl
   search     linearizable           4 node(s)
   yardstick  linearizable           3 order(s) tried
   verdict    the two checkers agree
   ```

   The yardstick refuses histories longer than 8 operations rather than
   pretending `9!` is a number you want to enumerate.

5. **A straddling write is allowed to land between two reads.** Reads that
   overlap a write need not see it. This is the case naive "the read must
   return the last completed write" checkers get wrong:

   ```console
   $ uv run linearize check --history fixtures/straddle.jsonl
   verdict    linearizable
   reason     a witness order of 3 operation(s) exists
   search     4 node(s), 0 memo hit(s), 3 operation(s)
   witness    one order that holds:
     1  client 1 read 0 [1, 2)
     2  client 0 write 1 [0, 10)
     3  client 1 read 1 [3, 4)
   ```

6. **The input is validated before it is believed.** A response before its
   invocation, two overlapping operations from one client, an unknown key, a
   negative instant — each is refused with the line number, because a history
   that cannot be ordered is not a history the checker can judge.

7. **The search is memoized on (remaining operations, current value).** Two
   paths that reach the same state reach the same answer; the memo is what
   keeps a refused history from being re-explored into a timeout.

## Commands

| command | what it does | exit |
| --- | --- | --- |
| `check --history FILE` | decide, with a witness or a core | 0 linearizable, 1 refused, 2 unusable input |
| `shrink --history FILE` | print only the core and its size | 1 on a refused history, 0 when there is nothing to shrink |
| `compare --history FILE` | search against the exhaustive yardstick | 0 agree, 1 disagree, 2 unusable |
| `demo` | six stories, each asserted | 0 |
| `selftest` | 45 checks over the modules and the command | 0 |

Useful options: `--initial N` when the register does not start at `0`,
`--json` on `check` and `shrink` for a payload with `linearizable`, `order`,
`nodes`, `memo_hits`, `reason` and `operations`.

## The history format

One JSON object per line, blank lines and `#` comments ignored:

```json
{"client": 0, "op": "write", "value": 5, "start": 0, "end": 2}
{"client": 1, "op": "read",  "value": 0, "start": 1, "end": 2}
{"initial": 0}
```

* `client` — who issued it; one value per client.
* `op` — `read` or `write`.
* `value` — the value written, or the value the read returned.
* `start` / `end` — whole-number instants; the operation was invoked at
  `start` and answered at `end`, so its interval is `[start, end)`.
* `{"initial": N}` — one optional header naming the register's starting value
  (`0` if absent).

## Demo

```console
$ uv run linearize demo
1. a sequential history has one order
...
6. the pruning is what makes the search finish
  seven operations: 7! = 5040 orders to try one at a time
  the search settled it in 8 node(s), the yardstick in 4321
  ok   the search visited far fewer nodes
stories      6 of 6 hold
```

## Layout

    src/{{ package_name }}/history.py   the format, the validation, the operations
    src/{{ package_name }}/check.py     the search, the yardstick, the shrinker
    src/{{ package_name }}/explain.py   the lines a verdict is printed as
    src/{{ package_name }}/demo.py      the six stories
    src/{{ package_name }}/cli.py       the command
    fixtures/                           three histories: legal, stale, straddling

## What this is not

* Not a model checker. It decides one register over a finite history, not a
  concurrent program over all its executions.
* Not a fault injector. It judges the history you hand it.
* Not a general-purpose ordering solver. There is no CAS, no queue, no
  multi-register object; a checker that pretends to cover those would need
  per-object semantics this one does not have.
