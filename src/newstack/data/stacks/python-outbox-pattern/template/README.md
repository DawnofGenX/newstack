# {{ title }}

Writing the row and then publishing the event is two operations, and the process
can die between them. The delete an outage causes is invisible: the order exists,
the customer was charged, and no consumer ever heard about it.

The outbox removes the gap by making the event a *row*: `INSERT INTO orders` and
`INSERT INTO outbox` commit in one `BEGIN IMMEDIATE`, so a crash loses both or
neither. A relay then publishes whatever is pending and marks it afterwards, which
is why delivery is at-least-once — and the consumer's ledger is what makes
"at-least-once" behave like "exactly once" for the effect.

## The three claims, in one command

```console
$ python -m {{ package_name }} demo
the write without an outbox        lost
    order 1 is committed, amount 1200
    outbox rows carrying the event: 0
    the order exists and nothing in the database says it happened
a crash between publish and mark   exactly once
    the sink accepted 2 copy/copies of 1 event
    pending after the crash: 1 (delivered 0)
    the consumer applied 1, dropped 1 repeat(s)
    the ledger total is 1200 for an order of 1200
a broker that refuses one aggregate in order
    first pass delivered 1, blocked 2
    blocked: seq 2 of order:1, behind seq 1
    second pass delivered 2 in seq order
    the consumer applied 3, last seq 2 for order:1
    the other aggregate was never held up: order:2
demo: 3 scenarios, 0 not as advertised
```

The first scenario is the negative control: the same write without an outbox,
observed to lose the event. The second is the crash window, observed to cost a
duplicate that the consumer absorbs. The third is ordering, observed to hold
because the relay holds the successor back instead of overtaking it.

## Quick start

```console
$ uv venv && uv pip install -e . pytest ruff
$ python -m {{ package_name }} place --amount 1200
placed  order 1 for 1200
event   a7e27ac9e5af4adf80e10312f73fc69d seq 1 (pending: 1)
$ python -m {{ package_name }} show
order    1      1200  placed
   1  pending    order:1      seq  1  order.placed   a7e27ac9e5af
1 order(s), 1 event(s) shown, 1 pending
$ python -m {{ package_name }} relay
publish a7e27ac9e5af4adf80e10312f73fc69d order:1 seq 1 {"aggregate": "order:1", ...}
relay   delivered 1, blocked 0
```

`relay --crash-after 1` publishes one event and dies before marking it, which is
the failure the tests care about most:

```console
$ python -m {{ package_name }} relay --crash-after 1
relay   delivered 0, blocked 0, crashed before marking a7e27ac9e5af
```

## Exit codes

| code | meaning |
| --- | --- |
| 0 | the command did its work; the relay left nothing pending |
| 1 | `relay` crashed or blocked an event; `demo` found a scenario that did not hold |
| 2 | a bad amount, an order that was already paid, an unusable database |

## Layout

| path | what it is |
| --- | --- |
| `src/<package>/model.py` | `Order`, `Event`, the envelope, canonical payload JSON |
| `src/<package>/store.py` | the two tables, one transaction, `unpublished`, `mark_published` |
| `src/<package>/relay.py` | `publish` with `crash_after` and per-aggregate blocking |
| `src/<package>/consumer.py` | the delivery ledger, the effect table, the order check |
| `src/<package>/demo.py` | the three scenarios, each with its own database |
| `smoke.sh` | 26 checks: the write, the relay, the crash, the demo, the refusals |

## Traps this stack exists to demonstrate

1. **"Write, then publish" is two writes.** The database transaction is the only
   atomic boundary you have; anything after `COMMIT` is a second operation, and a
   crash between the two is a lost event with nothing to report it.
2. **Publishing *before* committing is worse.** The consumer acts on an order that
   then rolls back — at-most-once with an invented fact, which no retry can undo.
3. **Marking after publishing is what makes it at-least-once.** Mark first and a
   crash after the mark loses the event silently; the mark is the acknowledgement,
   so it can only follow the acknowledgement.
4. **At-least-once means duplicates, in the design, not as an accident.** The
   consumer keeps `(consumer, event_id)` and applies the effect in the same
   transaction as the ledger row, so a duplicate is free and a crash mid-apply is
   not.
5. **Ordering is per aggregate and it costs something.** When the broker refuses
   one event, its successors must wait — `publish` tracks the stuck aggregates and
   reports them as `blocked`. Publishing `seq 2` because `seq 1` failed is how a
   consumer sees a payment before the order.
6. **The sequence number must be computed inside the transaction.** `SELECT
   COALESCE(MAX(seq), 0)` outside it lets two writers mint the same `seq`, and the
   unique index turns that into an intermittent error at 3am.
7. **An event id is created once and stored.** It has to exist before the insert so
   a redelivery is recognisable; generating it at publish time makes every retry
   look like new work.
8. **The outbox is a log, not a queue.** Published rows stay: they are the evidence
   that the event happened, and deleting them re-opens the question "was it
   published?" for anyone auditing. Retention is a policy, not a cleanup `DELETE`.
9. **A relay that only reads `WHERE published_at IS NULL` needs an index for it.**
   The partial index here is why the pending query stays cheap as the log grows.
10. **The demo needs its own databases.** Rebuilding one database for two scenarios
    carries state between them, and the second observation stops being independent.

## What this is not

One process, one database. The relay is not a competing-consumer group, the sink
is not a broker, and there is no schema registry — the point is the transaction
boundary and the two delivery guarantees, both of which are properties you have to
get right before a real broker helps.
