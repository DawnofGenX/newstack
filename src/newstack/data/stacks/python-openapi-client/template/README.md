# {{ title }}

A client built from an OpenAPI document, which checks both directions:

* the request it is about to send against the `requestBody` schema, and
* the response it just received against the schema for *that status code*.

When the server and the document disagree, the call fails with the member and the
reason, instead of handing back a value the caller will misread:

```
$ {{ npm_name }} call listNotes
drift  listNotes: the response does not fit the document
       $[0].tags: expected array, got integer
       $[0]: unexpected member 'server_side'
       $[0].priority: 'urgent' is not one of 'high', 'low', 'normal'
```

No dependencies, no generated code, no codegen step to keep in sync: the document is
read at run time, so editing the document is the whole of the "regeneration".

## Quick start

```bash
uv venv --allow-existing .venv && uv pip install --python .venv/bin/python -e . pytest ruff
.venv/bin/python -m {{ package_name }} list
PY=.venv/bin/python bash smoke.sh
```

`smoke.sh` starts two copies of `fixtures/server.py` — one that obeys
`fixtures/openapi.json` on port 5473 and one that has drifted from it on port 5474 — and
shows both outcomes.

## Commands

```
{{ npm_name }} list
{{ npm_name }} call OPERATION [--param NAME=VALUE]... [--body FILE|-] [--json]
{{ npm_name }} validate --operation OPERATION --response FILE [--status N]
{{ npm_name }} selftest
```

`--base-url` overrides the `servers` entry in the document. `validate` is the offline
half: it checks a response body you captured earlier, so an incident can be turned into
a regression test without the server being up.

## Exit codes

| code | meaning |
| --- | --- |
| 0 | the request and the response both fit the document |
| 1 | they do not — the problems are printed one per line |
| 2 | the tool could not be used: bad arguments, unreadable document, dead server |

Exit 1 is drift; exit 2 is your own mistake. A CI job that gates on this one code can
tell "the API changed" from "the pipeline is broken".

## The traps this stack exists to demonstrate

**`true` is not an integer.** `isinstance(True, int)` is `True` in Python, so a validator
that checks `isinstance(value, int)` accepts a boolean where the schema says integer.
`type_name()` names booleans first, and `same_value()` keeps `True` out of an enum that
lists `1`.

**A schema is chosen by status, not by operation.** A 404 with `{"error": "not_found"}`
is a valid answer if the document says so; a 200 with that body is drift. Checking
against "the" response schema silently accepts the wrong one.

**A status the document never lists is drift.** It is tempting to skip validation for
unknown statuses. That is exactly where new behaviour appears first.

**Path values must be percent-encoded.** An id of `a/b` becomes two path segments and
`a?b=c` becomes a query string, so the request lands somewhere no path in the document
describes. `quote(value, safe="")` is not decoration.

**An error body still has a schema.** `urllib` raises `HTTPError` for 4xx and 5xx; the
default transport unpacks it so the body can be validated like any other.

**A request can be wrong before it is sent.** Validating only responses means a typo in
a field name reaches production once per call. `call` refuses an invalid body with exit
1 and never opens the socket.

**`$ref` resolution is not optional.** Real documents put nearly everything behind
`#/components/schemas/...`; a validator that only understands inline schemas validates
almost nothing.

## Layout

```
fixtures/openapi.json      the contract, and the only source of truth
fixtures/server.py         a server that obeys it, and one that does not (--drift)
src/{{ package_name }}/schema.py    the JSON Schema subset an OpenAPI doc needs
src/{{ package_name }}/spec.py      load the document, build operations and URLs
src/{{ package_name }}/client.py    transport, request/response validation, DriftError
src/{{ package_name }}/cli.py       the commands and the exit codes
src/{{ package_name }}/selftest.py  checks the checker against two live servers
```
