# {{ title }}

{{ description }}

An ignore file is a small language with a surprising amount of behaviour in it:
patterns anchor at the root when they contain a slash, a trailing slash means
"directory only", the **last** rule that matches wins, and a negation cannot
rescue a file whose parent directory is excluded. `{{ npm_name }}` reads the
file the way git reads it and tells you *which line* decided — so "why is this
file ignored?" has an answer other than a shrug.

## The rules this tool takes literally

1. **A pattern with a slash is anchored to the root.** `build` ignores any
   directory named `build` at any depth; `/build` ignores only the one at the
   top. Trailing spaces are dropped unless a backslash protects them.
2. **A trailing slash names a directory.** `build/` ignores the directory; a
   *file* called `build` is untouched. Everything under the directory follows
   through the ancestor rule, not through the pattern.
3. **The last matching rule wins.** A negation is an ordinary rule that happens
   to say "not ignored" — it only rescues a path if nothing later contradicts
   it, which is why `*.log` after `!keep.log` re-ignores `keep.log`.
4. **An excluded parent cannot be undone.** If `build/` ignores the directory,
   `!build/keep.txt` cannot re-include a file inside it. Git never looks inside
   an excluded directory, so neither does this tool: the verdict names the
   parent instead of pretending the negation worked.
5. **One star stops at a slash; two do not.** `logs/*.log` reaches one level,
   `logs/**/*.log` crosses directories, and a leading `**/` also matches the
   root.
6. **`?`, classes and escapes are literal.** `temp?.md` needs exactly one
   character, `file[0-9].txt` takes one digit, `file[!0-9].txt` refuses digits,
   and `\!name` or `\#name` are file names rather than a negation or a comment.

## Quick start

```bash
cd your-project
uv venv --allow-existing .venv
uv pip install --python .venv/bin/python -e . pytest ruff
.venv/bin/python -m {{ package_name }} explain build/out/app.js
```

## Commands

Everything takes `--ignore PATH` (default `.gitignore`) and prints a verdict
that names the deciding line.

```console
$ {{ npm_name }} explain build/out/app.js --ignore fixtures/.gitignore
ignore     fixtures/.gitignore
path       build/out/app.js
kind       file
verdict    ignored
rule       line 7: build/
reason     its parent 'build' is ignored by line 7, and a file cannot be re-included while its parent is excluded
```

A negation is reported as the rule that decided, and the exit code follows the
verdict rather than the message:

```console
$ {{ npm_name }} explain release.log --ignore fixtures/.gitignore
ignore     fixtures/.gitignore
path       release.log
kind       file
verdict    not ignored
rule       line 13: !release.log
reason     line 13 is a negation and it is the last rule that matches
$ echo $?
0
```

`build` as a *file* is not the directory `build/`, so nothing matches it:

```console
$ {{ npm_name }} explain build --ignore fixtures/.gitignore
path       build
kind       file
verdict    not ignored
reason     no rule matched, so there is nothing to ignore
```

`list` shows every rule that was read, with the flags that change its meaning:

```console
$ {{ npm_name }} list --ignore fixtures/.gitignore
ignore     fixtures/.gitignore
rules      14
   2       node_modules/  [directory only]
   3       .venv/  [directory only]
   4       __pycache__/  [directory only]
   7       build/  [directory only]
   8       dist/  [directory only]
   9       *.egg-info/  [directory only]
  12       *.log
  13       !release.log  [negation]
  16       .DS_Store
  17       *.swp
  18       *~
  21       .env
  22       !env.example  [negation]
  25       !fixtures/**  [negation, anchored]
```

`walk` decides every path under a directory — directories included, because a
directory is a path that can be ignored too:

```console
$ {{ npm_name }} walk . --ignore fixtures/.gitignore --all
ignore     fixtures/.gitignore
root       .
paths      7
ignored    4
ignored    app.log  (line 12)
ignored    build  (line 7)
ignored    build/sub  (line 7)
ignored    build/sub/app.js  (line 7)
tracked    src  (no rule)
tracked    src/main.py  (no rule)
tracked    fixtures/data.json  (line 25)
```

`--json` turns any of these into a payload with the same fields, and `demo` runs
the six stories (`selftest` runs the same checks non-interactively):

```console
$ {{ npm_name }} demo | tail -3
6. a negation cannot rescue a file inside an excluded directory
  ...
stories      6 of 6 hold
```

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | the path is **not** ignored |
| 1 | the path **is** ignored |
| 2 | the question could not be answered (missing file, bad pattern, a path outside the tree) |

`explain` exits 1 on an ignored path on purpose: `if {{ npm_name }} explain "$f"; then echo kept; fi`
is a shell pipeline that reads well. Errors are 2, so they never look like a verdict.

## Layout

```
src/{{ package_name }}/pattern.py   one line -> Rule(text, body, line, negated, dir_only, anchored, regex)
src/{{ package_name }}/matcher.py   Rule[] -> Verdict, with the ancestor rule applied first
src/{{ package_name }}/demo.py      the six stories, each asserted
src/{{ package_name }}/selftest.py  the same checks plus the command line, no shell needed
src/{{ package_name }}/cli.py       explain / list / walk / demo / selftest
fixtures/.gitignore                 a realistic ignore file the examples run against
fixtures/paths.txt                  paths that exercise every rule in it
```

## What this is not

- Not a git implementation. It never touches an index, never asks git for its
  opinion, and never runs `git check-ignore`.
- Not a filesystem walker with caching or watching: `walk` is a `rglob` and a
  verdict per path, which is enough to explain a tree and not enough to be a
  watcher.
- Not a `.gitignore` *writer*: there is no command that edits the file.

## Tests

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m {{ package_name }} selftest
PY=.venv/bin/python bash smoke.sh
```

The test suite pins the parsing rules, the ancestor rule, and the exit codes;
`smoke.sh` runs the real commands against `fixtures/.gitignore` and checks the
numbers the README promises.

## Licence

MIT. See `LICENSE`.
