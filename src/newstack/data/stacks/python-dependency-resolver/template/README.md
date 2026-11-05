# {{ title }}

{{ description }}

{{ npm_name }} reads a package index, picks one version per package, and prints why.
When it cannot, it prints the dead ends instead of a best-effort tree — because a
best-effort tree is how two machines install the same project differently.

## The rules this resolver keeps

1. **Semantic versions are ordered by precedence, not by text.** `1.0.0-alpha < 1.0.0-alpha.1
   < 1.0.0-rc.1 < 1.0.0`, numeric identifiers compare as numbers (`beta.11 > beta.2`), and
   build metadata is ignored: `1.0.0+a` and `1.0.0+b` are the same version, so the index
   refuses to publish both.
2. **A caret below 1.0.0 is not "same major".** `^1.2.3` allows `1.x.y`, `^0.2.3` allows only
   `0.2.x`, `^0.0.3` only `0.0.3`, and a bare `^0` means anything before `1.0.0`. Below 1.0.0
   the leftmost non-zero part is the part the author promised not to break.
3. **A prerelease is opt-in.** `>=1.0.0` does not take `1.1.0-rc.1`, and `^2.0.0` does not take
   `3.0.0-rc.1`. Only a range that names that exact `major.minor.patch` in a prerelease form
   can select one.
4. **One version per package.** Two requirements on one package must intersect; when they
   cannot, that branch is abandoned and the failure names both ranges and who asked.
5. **Highest first, but backtrack.** A greedy resolver fails on the first diamond. This one
   tries the highest allowed version, and when a later requirement makes that choice
   impossible it walks back — including back over packages it had already chosen.
6. **The answer does not depend on the order you wrote the roots.** Pending packages are
   visited most-constrained first and ties break on name.
7. **A lockfile is a preference, not a cage.** The locked version is tried first, so an
   unchanged project keeps its tree; a `check` fails only when the lock no longer resolves
   (a stale or missing entry), never merely because a newer version was published.

## Quickstart

```console
$ uv venv --allow-existing .venv
$ uv pip install --python .venv/bin/python -e . pytest ruff
$ .venv/bin/python -m {{ package_name }} resolve --root web=^2.0.0 --root cli=^1.0.0
  cli                1.1.0        highest version that satisfies every range
  shared             1.4.0        highest version that satisfies every range
  web                2.0.0        highest version that satisfies every range
resolved 3 package(s) after exploring 4 partial solution(s)
```

The index fixture is deliberately a trap: `web 2.1.1` is the highest match for `^2.0.0`, but
it needs `shared ^2.0.0` while `cli` needs `shared ^1.0.0`. The printed answer is `web 2.0.0`,
which is the only version of `web` that can coexist with `cli`.

```console
$ .venv/bin/python -m {{ package_name }} why --root web=^2.0.0 shared
shared 1.4.0 — highest version that satisfies every range
  cli@1.1.0 needs shared ^1.0.0
  web@2.0.0 needs shared ^1.2.0
```

```console
$ .venv/bin/python -m {{ package_name }} check --root web=^2.0.0 --lock deps.lock.json
check: deps.lock.json still resolves; 2 package(s) agree
```

## What a conflict looks like

```console
$ .venv/bin/python -m {{ package_name }} resolve --root web=^2.1.0 --root cli=^1.0.0
{{ npm_name }}: no resolution exists. The search proved it by exhausting these dead ends:

cannot pick a version of shared:
  cli@1.1.0 needs shared ^1.0.0
  web@2.1.0 needs shared ^2.0.0
  published: 1.2.0, 1.4.0, 2.0.0, 3.0.0-rc.1
```

## The demo

```console
$ .venv/bin/python -m {{ package_name }} demo
```

Six stories: the greedy answer that fails, a conflict that names both ranges, prereleases
staying out unless asked, the caret at major zero, root order not changing the answer, and a
lock that holds a working tree still.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | resolved, or the lockfile is current |
| 1 | no resolution exists, or the lockfile has drifted |
| 2 | unusable input: a bad range, a bad index, an unknown root, a bad lockfile |

## Layout

```
src/{{ package_name }}/versions.py   precedence, and why build metadata is not comparable
src/{{ package_name }}/ranges.py     ^ ~ comparator ranges, the caret-at-zero rule, prerelease opt-in
src/{{ package_name }}/index.py      the published versions, validated before the search starts
src/{{ package_name }}/resolver.py   most-constrained-first backtracking with recorded dead ends
src/{{ package_name }}/lockfile.py   stable rendering, drift that matters, and drift that does not
```
