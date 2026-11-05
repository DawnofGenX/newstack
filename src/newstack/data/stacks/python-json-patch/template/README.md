# {{ title }}

JSON Pointer and JSON Patch, applied whole or not at all.

{{ description }}

## The rules this project keeps

1. **A pointer is parsed, not split.** `~1` is a slash and `~0` is a tilde, so a
   key that contains a slash stays one key. A splitter that ignores the escapes
   turns `/a~1b` into two keys and finds neither.
2. **A segment is an index only when its parent is a list.** `{"0": "x"}` holds
   the key `"0"`; `["x"]` holds the index `0`. `01` is neither, and `-` is the
   position after the end, so it can be written to but never read.
3. **`add` inserts, `remove` shifts.** Indices are positions, not identities:
   removing `/items/0` moves the element that was at `1` down to `0`.
4. **A patch applies whole or not at all.** Every operation runs against a copy.
   If any of them fails, the copy is discarded and the caller gets an error that
   names the operation, so a refusal leaves nothing half-done behind.
5. **`test` is how a patch says "only if".** It compares with JSON equality:
   `1` equals `1.0`, and `true` equals neither of them. A failing test refuses
   the patch and applies none of the operations around it.
6. **`move` removes before it adds, and `copy` is deep.** A move into the moved
   value's own child is refused, because the value would then contain itself.
7. **A diff has to prove itself.** `diff` computes a patch and the demo applies
   it, comparing the result with the document it was taken from. The patch is
   not guaranteed minimal; it is guaranteed to work.

## Try it

```console
$ {{ npm_name }} demo
1. a key that holds a slash is not two keys
  document        {"a/b": 1, "m~n": 2}
  pointer /a~1b   resolves to 1
  key 'm~n'       renders as /m~0n
  a splitter that ignores the escapes walks key 'a' then key 'b' and finds nothing: True
  -> holds

2. a numeric key is not an index
  the same pointer on an object: "an object key"
  the same pointer on a list:   "the first element"
  refused /01: '01' is not an array index: a leading zero is not allowed
  refused /-: '-' names the position after the last element, so it has no value to read
  -> holds

3. add inserts and remove shifts
  start           {"items": ["a", "c"]}
  add /items/1 b  {"items": ["a", "b", "c"]}
  remove /items/0 {"items": ["b", "c"]}
  add /items/- d  {"items": ["b", "c", "d"]}
  indices are positions, not identities: the element that was at 1 is now at 0
  -> holds
```

Story 4 is the one that shows atomicity: the patch is

```
test /version == 3, then replace /value
```

and against a document whose version is `2` it prints

```
refused         operation 1 (test) failed, so nothing was applied: test failed at '/version': the document holds 2 and the patch expected 3
document after  {"value": "old", "version": 2}
```

Story 5 fails on the *second* of three operations, and the first one is rolled
back with it: `'b'` is absent from the document afterwards. Story 6 computes a
seven-operation diff between `fixtures/document.json` and
`fixtures/after.json`, applies it, and compares.

## Applying a patch

```console
$ {{ npm_name }} apply --document fixtures/document.json --patch fixtures/changes.json
operations   7
    1. test     /version  3
    2. replace  /version  4
    3. replace  /items/1/qty  5
    4. add      /items/-  {"id": 3, "qty": 1}
    5. remove   /meta/m~0n
    6. copy     /slug  from /name
    7. move     /items/0/ref  from /items/0/id
result
{
  "items": [
    {
      "qty": 2,
      "ref": 1
    },
    {
      "id": 2,
      "qty": 5
    },
    {
      "id": 3,
      "qty": 1
    }
  ],
  "meta": {
    "a/b": "slash"
  },
  "name": "orders",
  "slug": "orders",
  "version": 4
}
$ echo $?
0
```

`check` applies the same patch and throws the result away: the useful half of
"would this work?" without touching the file.

## Reading one value

```console
$ {{ npm_name }} resolve --document fixtures/document.json "/meta/m~0n"
pointer      /meta/m~0n
value        "tilde"
$ {{ npm_name }} resolve --document fixtures/document.json "/meta/a~1b"
pointer      /meta/a~1b
value        "slash"
$ {{ npm_name }} resolve --document fixtures/document.json "/meta~2n"
{{ npm_name }}: error: invalid escape '~' in 'meta~2n': only ~0 and ~1 are defined, so this segment cannot be unescaped without guessing
$ echo $?
2
```

## Writing a patch between two documents

```console
$ {{ npm_name }} diff --before fixtures/document.json --after fixtures/after.json
operations   7
    1. replace  /version  4
    2. remove   /items/0/id
    3. add      /items/0/ref  1
    4. replace  /items/1/qty  5
    5. add      /items/-  {"id": 3, "qty": 1}
    6. remove   /meta/m~0n
    7. add      /slug  "orders"
applies      True
```

`applies True` is computed, not printed by hand: the tool applies its own patch
and compares the result with the second document.

## Use it in code

```python
from {{ package_name }}.patch import PatchError, apply
from {{ package_name }}.pointer import PointerError, resolve

value = resolve(document, "/items/0/id")
try:
    updated = apply(document, [
        {"op": "test", "path": "/version", "value": 3},
        {"op": "replace", "path": "/version", "value": 4},
    ])
except PatchError as error:
    ...  # nothing was applied, and `document` is untouched
```

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | the patch applied, or the value was read |
| 1 | the patch refused: a test failed, or an operation did not apply |
| 2 | the input could not be read, or the pointer is not a pointer |

## Layout

```
src/{{ package_name }}/
  pointer.py   RFC 6901: escape, parse, render, resolve
  patch.py     RFC 6902: the six operations, applied atomically
  diff.py      a patch between two documents, plus its self-check
  demo.py      the six stories
  cli.py       apply / check / resolve / diff / demo / selftest
tests/         pytest, one file per module
fixtures/      document.json, changes.json, after.json
```

## Verify it yourself

```console
$ uv venv
$ uv pip install -e . pytest ruff
$ .venv/bin/pytest -q
$ .venv/bin/ruff check .
$ .venv/bin/python -m {{ package_name }} selftest
$ bash smoke.sh
```

## What this project does not do

- It does not compute a minimal patch. `diff` favours an obviously correct
  patch over the smallest one.
- It does not merge patches, and it has no notion of a "merge patch"
  (RFC 7386) — that is a different format with different rules.
- It does not store documents. Ordering and atomicity are here; durability is
  your store's problem.

## License

MIT. See LICENSE.
