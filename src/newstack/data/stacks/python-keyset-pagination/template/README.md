# {{ title }}

`LIMIT 20 OFFSET 40` pages over a moving table by counting rows, so the row that
was 40th a moment ago is 39th now — and it is skipped, or read twice, and nobody
is told. This stack pages by *position* instead: the cursor carries the sort value
and the id of the last row you saw, and the next page is `WHERE (sort_key, id) >
(?, ?)`. A delete or an insert anywhere else cannot move you.

The demo proves it on SQLite in one command, and the numbers are computed from
the rows that came back:

```console
$ python -m {{ package_name }} seed --count 30
seeded 30 item(s) into items.db
$ python -m {{ package_name }} demo
a row the client already saw is deleted cursor clean   offset: skipped 1, repeated 0
    rows walked: cursor 30, offset 29 of 30 that exist
    offset never returned row(s) [7]
    offset returned row(s) none twice
    the deleted row was on page 1, so no later page can be blamed for missing it
a row is inserted before the cursor cursor clean   offset: skipped 0, repeated 1
    rows walked: cursor 30, offset 31 of 30 that exist
    offset never returned row(s) none
    offset returned row(s) [6] twice
    the new row sorts before the position, so a cursor rightly never shows it
demo: 2 scenarios, 0 cursor problem(s), 0 offset walk(s) that survived
```

## Quick start

```console
$ uv venv && uv pip install -e . pytest ruff
$ python -m {{ package_name }} seed --count 30
$ python -m {{ package_name }} page --size 3
   0  1700000000  note 000
   1  1700000000  note 001
   2  1700000000  note 002
page    3 row(s); next eyJpZC...
$ python -m {{ package_name }} scan --size 10
0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29
scanned 30 row(s), 0 duplicate(s), 0 missing
```

`scan` is the gate: it walks every page and compares what it saw against
`SELECT id ... ORDER BY` — the one query it is trying to prove. Exit `0` means
no row was skipped and none was returned twice.

## The cursor

```console
$ python -m {{ package_name }} page --size 7 --json
{
  "rows": [
    {"id": 0, "created_at": 1700000000, "title": "note 000"},
    ...
  ],
  "next_cursor": "eyJpZC...",
  "prev_cursor": null,
  "query": "c18468412df4",
  "size": 7
}
```

The cursor is base64url JSON of `{"v": 1, "sort": ..., "id": ..., "query": ...}`
with no padding. It is opaque on purpose — the client should not be able to
construct one — but it is not secret, and it is not a token: see the traps.

## Exit codes

| code | meaning |
| --- | --- |
| 0 | the page, the scan, or the demo succeeded |
| 1 | `scan` found a duplicate or a missing row; `demo` found the contrast missing |
| 2 | a bad cursor, a bad size, an unknown sort key, an unusable database |

## Layout

| path | what it is |
| --- | --- |
| `src/<package>/model.py` | `Order`, `Query`, `Cursor`, `Page` — and the cursor encoding |
| `src/<package>/store.py` | SQLite with the one query shape that pages, plus OFFSET for the demo |
| `src/<package>/pager.py` | `page`, `scan`, `walk`, and the duplicate/missing report |
| `src/<package>/demo.py` | the deletion and the insertion, walked twice each |
| `src/<package>/cli.py` | `seed`, `page`, `scan`, `demo`, `selftest` |
| `smoke.sh` | 18 checks: page, cursor, contrast, refusals |

## Traps this stack exists to demonstrate

1. **A cursor names a position, not an offset.** Rows are inserted and deleted
   while a user pages; the number 40 means nothing the moment the table changes.
   `(sort_key, id) > (?, ?)` means "after this row", which stays true.
2. **The sort key alone is not an order.** `created_at` ties — the seeded
   population ties every four rows on purpose — and ties in an unordered set have
   no stable position, so the same row can appear on two pages. Every order here
   is `(key, id)`, and the id breaks the tie the same way on every machine.
3. **A cursor is bound to the query that made it.** Reusing a cursor after
   changing the filter or the sort returns a plausible-looking page from a
   different result set. The fingerprint is checked:
   `cursor was made for a different query (c18468412df4 != 438941804bc0)`.
4. **`LIMIT size + 1` answers "is there more?" without a second query.** A
   `COUNT(*)` after the page answers about a later moment, which is how "page 3
   of 4" pages disappear.
5. **`OFFSET` is not wrong because it is slow.** It is wrong because it counts.
   The demo's skipped id `[7]` is a row that no client will ever see, and nothing
   in the response says so.
6. **Backwards paging flips both comparisons and the order.** `direction=backward`
   reads `<` with `ORDER BY ... DESC`, then reverses the rows, so `prev_cursor`
   means the same thing as `next_cursor` in the other direction.
7. **A cursor is not a permission.** It is base64url JSON, so anyone can edit the
   sort value and jump anywhere — which is fine for public listings and is not
   fine for "show me the rows after my own last one". Sign it if it must mean
   "where the user was", not "where the query is".
8. **An empty page is not the end of the world.** A missing database is created,
   an empty table pages to `0 row(s)`, and `next_cursor` is `null` — the caller
   should stop on the null, not on the row count.

## What this is not

No keyset uniqueness beyond `(key, id)`, no join handling, no snapshot isolation:
if a row's sort value is *updated* to somewhere ahead of the cursor, it will be
seen twice — keyset is stable against inserts and deletes, not against moving the
sort key itself. If that matters, order by an immutable column, which is the same
advice as "do not page by `updated_at`".
