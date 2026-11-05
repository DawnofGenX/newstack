# {{ title }}

A unified diff that parses, applies, and refuses to guess.

Most patch code trusts the hunk header. This one does not: every hunk is located
against the text it actually lands on, so a hunk that has drifted still applies,
a hunk that matches in two places is an error, and fuzz is reported instead of
quietly rewriting a line. Then `check` proves the only statement that matters —
`apply(old, diff(old, new)) == new` — before a deploy tool trusts it.

No dependencies outside the standard library.

## Quick start

```
uv venv
uv pip install -e . pytest ruff

$ {{ npm_name }} diff a.txt b.txt
--- a.txt
+++ b.txt
@@ -1,3 +1,3 @@
 line 1
-line 2
+line two
 line 3

$ {{ npm_name }} diff a.txt b.txt -o change.patch
wrote      change.patch: a.txt -> b.txt: 1 hunk(s), +1 -1

$ {{ npm_name }} apply a.txt change.patch
line 1
line two
line 3

$ {{ npm_name }} check a.txt b.txt
ok   the patch parses             1 hunk(s)
ok   apply reproduces the new text identical
ok   diffing the result is empty  no hunks
verdict   all three claims hold

$ {{ npm_name }} demo
...
demo: 7 scenarios, 0 not as advertised

$ PY=.venv/bin/python bash smoke.sh
47 passed, 0 failed
smoke: all checks passed
```

## Commands

```
diff OLD NEW [--context N] [-o OUT]   write a patch, or print it
apply FILE PATCH [--fuzz N] [-i]      apply it, print the result or rewrite FILE
check OLD NEW [--context N]           prove apply(OLD, diff(OLD, NEW)) == NEW
demo                                  seven refusals and successes, live
selftest                              the same claims, without the prose
```

Exit codes: `0` success, `1` a claim in `check` broke, `2` unusable input
(bad patch, missing file, out-of-range option).

## The demo, verbatim

```
the round trip holds                   as advertised
  ok   the patch parses             1 hunk(s)
  ok   apply reproduces the new text identical
  ok   diffing the result is empty  no hunks
  every claim above is a computation, not a comment

a hunk that matches twice              as advertised
  the patch says line 5; this text has two matching blocks at lines 1 and 2
  ApplyError: hunk 1 matches at lines 1 and 2: the patch does not say which one, and guessing would corrupt one of them
  refusing is the point: picking the first would silently edit the wrong block

a hunk whose lines have moved          as advertised
  applied   clean
  the hunk said line 3; the context was found at line 5 (6)
  each hunk is remeasured against the text it lands on, so earlier edits do not make later hunks miss

a context line that changed            as advertised
  ApplyError: hunk 1 does not apply: line 1 is 'start', the patch expects 'line 1'
  a patch that does not fit is not a patch to force

fuzz hides a context edit              as advertised
  strict: ApplyError: hunk 1 does not apply: line 3 is 'line three', the patch expects 'line 3'
  fuzz=1: applied   with fuzz: hunk 1 dropped 1
  the tolerated line is kept from the file, not from the patch: 'line three'
  fuzz is a report, not a silent repair, and this is why patch(1) says 'with fuzz'

no newline at end of file              as advertised
  the patch carries the marker: '\\ No newline at end of file'
  applying it gives 'a\nc' — no newline invented, none dropped
  a diff that cannot tell 'a\n' from 'a' rewrites the last line of every file

the same patch applied twice           as advertised
  applying a patch once is the normal case; applying it twice is the accident
  ApplyError: hunk 1 does not apply: line 7 is 'line seven', the patch expects 'line 7'
  the second run refuses because the text it expected is gone — which is exactly the check that catches a retried deployment step

demo: 7 scenarios, 0 not as advertised
```

## Five things that go wrong, and what this does instead

1. **A hunk that matches twice is a coin flip.** Two identical blocks and a
   hunk with no context to tell them apart: the tool errors with both line
   numbers. Picking the first match is how a deploy edits the wrong function.
2. **Hunk offsets drift.** Line numbers in a patch are hints from the file the
   patch was made against. Every hunk is remeasured against the text it lands
   on, so an earlier hunk that shifted everything still lets the later ones
   apply — and the report says where the context was found.
3. **Fuzz can hide a real edit.** With `--fuzz 1` a hunk may apply while
   dropping a context line that no longer matches. That is allowed, printed
   (`with fuzz: hunk 1 dropped 1`), and the tolerated line is kept **from the
   file**, not from the patch.
4. **`a\n` and `a` are different files.** A diff that cannot say "no newline at
   end of file" rewrites the last line of every file it touches. The marker is
   written, parsed, and applied.
5. **Text mode eats the endings.** Reading with `read_text()` translates CRLF to
   LF, which is exactly the difference a diff is supposed to preserve. The CLI
   reads and writes **bytes**.

## What this is not

Not a merge tool, not a three-way patcher, not git. It applies one file per
patch, refuses patches with two `---` headers, and does not touch the index.
There is no binary support: a patch that is not UTF-8 is an error, not a guess.

## Layout

| path | what it holds |
| --- | --- |
| `src/{{ package_name }}/model.py` | `Hunk`, `FilePatch`, the splitter, `DiffError` |
| `src/{{ package_name }}/diff.py` | `diff_lines`, `format_patch`, `parse_patch` |
| `src/{{ package_name }}/apply.py` | `apply_text`: locate, tolerate, refuse |
| `src/{{ package_name }}/verify.py` | the three `check` claims |
| `src/{{ package_name }}/demo.py` | the seven scenarios above |
| `src/{{ package_name }}/cli.py` | `diff`, `apply`, `check`, `demo`, `selftest` |
