# {{ title }}

A router where the walk itself is the rule: at every segment a literal beats a
parameter, a parameter beats a catch-all, and when a branch dead-ends the matcher
backs out and tries the next one instead of reporting a miss. A wrong method is
never reported as a missing resource.

## Why the walk order is the feature

A route table is not a set of predicates that each get tested; it is a tree you
descend. The order a trie descends decides which route answers, so that order has
to be stated, tested and explainable:

1. **A literal beats a parameter.** `GET /users/me` and `GET /users/{id}` both
   describe one segment. `/users/me` goes to the literal every time.
2. **A parameter beats a catch-all.** `/files/{name}` takes one segment,
   `/files/*rest` takes the rest. One segment is more specific than "the rest".
3. **A dead branch is abandoned, not fatal.** With `/a/b/d` and `/a/{x}/c`
   registered, `/a/b/c` walks into the literal `b` branch, finds nothing below it,
   and backs out to the parameter branch. A matcher that stops at the first failed
   descent turns a reachable route into a 404.
4. **The first divergence decides.** `/a/{x}/c` and `/a/b/{y}` both match
   `/a/b/c`. They differ at segment 2, where `b` is a literal in the second, so
   the second wins — depth of the literal, not length of the pattern.
5. **A wrong method is not a missing path.** If a path matches routes for other
   methods, the answer is `not-allowed` with the methods that would have worked,
   never `no route`.
6. **A miss explains the segment that ended the walk.** The reason names the
   segment that had no continuation and the literals that were available, plus a
   hint at the nearest registered route.
7. **Nothing is silently normalised.** `/users/42/` and `//users` are refused with
   a reason, not trimmed into something else; a second route on one shape and
   method is refused rather than overwriting the first.

## Quick start

    cd your-project
    uv sync
    uv run {{ npm_name }} table --routes fixtures/routes.txt

```text
10 route(s)
  GET     /                  (root)
  GET     /files/*rest       static catchall
  GET     /files/{name}      static param
  GET     /health            static
  GET     /users/me          static static
  DELETE  /users/{id}        static param
  GET     /users/{id}        static param
  PUT     /users/{id}        static param
  GET     /users/{id}/posts  static param static
  POST    /users/{id}/posts  static param static
```

The last column is the pattern shape: what each segment is, left to right.

## Commands

`match` asks the router one question and prints what happened:

```console
$ uv run {{ npm_name }} match --routes fixtures/routes.txt --path /users/42/posts
method     GET
path       /users/42/posts
verdict    matched
route      GET /users/{id}/posts
param      id = '42'
```

A miss exits 1 and says which segment stopped the walk:

```console
$ uv run {{ npm_name }} match --routes fixtures/routes.txt --path /users/42/comments
method     GET
path       /users/42/comments
verdict    no route
reason     segment 3 of the path is 'comments', and the literals here are 'posts'
hint       GET /users/{id}/posts shares 1 segment(s) with this path
```

A wrong method exits 1 and lists what would have worked:

```console
$ uv run {{ npm_name }} match --routes fixtures/routes.txt --method PATCH --path /users/42
method     PATCH
path       /users/42
verdict    wrong method
allow      DELETE, GET, PUT
reason     the path matches 3 route(s) for another method, so this is DELETE, GET, PUT and not a missing resource
```

`why` prints every method that was tried, in order, so the walk is visible:

```console
$ uv run {{ npm_name }} why --routes fixtures/routes.txt --method PATCH --path /users/42
verdict    not-allowed
reason     the path matches 3 route(s) for another method, so this is DELETE, GET, PUT and not a missing resource
allow      DELETE, GET, PUT
tried
  GET     match  GET /users/{id}
```

`table` lists the registry, and both `match` and `table` take `--json`:

```console
$ uv run {{ npm_name }} match --routes fixtures/routes.txt --path /files/2026/11/a.txt --json
{
  "kind": "match",
  "method": "GET",
  "path": "/files/2026/11/a.txt",
  "route": "GET /files/*rest",
  "name": "",
  "params": {
    "rest": "2026/11/a.txt"
  }
}
```

`demo` walks six stories about the order, and `selftest` runs the invariants
against a live router:

```console
$ uv run {{ npm_name }} demo | tail -1
stories      6 of 6 hold

$ uv run {{ npm_name }} selftest | tail -1
selftest: 68 checks passed, 0 failed
```

## The route file

One route per line, `METHOD /pattern`, `#` for comments, blanks skipped:

    GET /users/me
    GET /users/{id}
    PUT /users/{id}
    GET /files/*rest

Segment kinds: a literal (`users`), a parameter (`{id}`) or a catch-all (`*rest`,
which must be the last segment). A parameter name must be a lower-case identifier
and may appear once per pattern.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | the path matched (or the command ran: `table`, `demo`, `selftest`) |
| 1 | no route, or a path that exists only for other methods |
| 2 | the question itself was unusable: bad pattern, missing file, unknown method |

Exit 2 is for the caller's mistake, not the router's answer: a path that cannot
be a path is not a miss.

## Files

    src/{{ package_name }}/pattern.py    segments, patterns, path splitting
    src/{{ package_name }}/router.py     the trie, the walk, resolutions
    src/{{ package_name }}/explain.py    how a resolution is printed
    src/{{ package_name }}/demo.py       six stories about the order
    src/{{ package_name }}/cli.py        match, table, why, demo, selftest
    fixtures/routes.txt                  the table used by the smoke test

## Non-goals

- No path rewriting, redirects or trailing-slash tolerance: the router answers
  about the path it was given.
- No regex segments. If a segment needs a pattern, it needs a route of its own.
- No HTTP server. This is the table and the walk; wiring it to a socket is the
  caller's job.
