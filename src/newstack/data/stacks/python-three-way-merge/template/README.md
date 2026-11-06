# {{ title }}

{{ description }}

A three-way merge answers one question per region of the base file: what did each
side do here? When only one side touched the region, that side wins. When both
touched it, the merge either finds they made the same edit or writes a conflict.
Everything else -- picking a winner, reordering insertions, "fuzzy" matching --
is a guess, and a guess about text is indistinguishable from a bug until it has
shipped.

```console
$ {{ npm_name }} merge --base fixtures/base.txt --ours fixtures/ours.txt --theirs fixtures/theirs.txt
service: checkout
replicas: 4
image: checkout:1.5.0
health:
  path: /healthz
  port: 8080
log:
<<<<<<< ours
  level: debug
=======
  level: warn
>>>>>>> theirs
  format: json
merge      chunks 6: 2 change(s) from ours, 2 from theirs, 0 agreed, 1 conflict(s)
```

Two clean changes and one disagreement. The replicas change came from ours, the
image change from theirs, and only the log level -- which both sides rewrote --
is in dispute.

## Quick start

```bash
cd your-project
uv sync
uv run {{ npm_name }} demo
uv run {{ npm_name }} merge --base fixtures/base.txt --ours fixtures/ours.txt --theirs fixtures/theirs.txt
PY=.venv/bin/python bash smoke.sh
```

## The rules this merge keeps

1. **A conflict is the region both sides changed, and nothing more.** Everything
   outside it is merged. A tool that marks the whole file conflicted has thrown
   away the work it was supposed to do.
2. **The same edit on both sides is agreement, not a conflict.** Identical text
   is not a decision to make, so it appears once and the chunk is reported as
   `both`.
3. **Two insertions at the same point have no order, so they conflict.** Nothing
   in the base says which line comes first. Two insertions at *different* points
   are ordered by the base and merge cleanly.
4. **An insertion beside a replacement at the same line does not conflict.** An
   insertion consumes no base line, so it goes before the line it precedes; the
   replacement then replaces that line. The order is in the base, not invented.
   An insertion at the boundary *after* a replaced line is likewise separate.
5. **Markers always start their own line.** If a conflicting span is a file
   without a final newline, the merge terminates that line before writing
   `=======`, because a marker glued to text is not a marker a tool can parse.
6. **An empty base is not a special case.** One side's text is the answer; two
   different texts are a conflict.
7. **`explain` shows the answer before it shows the text.** Every chunk is
   listed with its kind, its base range, and its size, so a surprising merge can
   be read rather than guessed at:

```console
$ {{ npm_name }} explain --base fixtures/clean-base.txt --ours fixtures/clean-ours.txt --theirs fixtures/clean-theirs.txt
merge      chunks 4: 1 change(s) from ours, 1 from theirs, 0 agreed, 0 conflict(s)
 1  same     base 0..2       2 line(s)  first line '# changelog'
 2  ours     base 2..3       1 line(s)  first line '## 1.5.0'
 3  same     base 3..5       2 line(s)  first line '- checkout'
 4  theirs   base at 5       1 line(s)  first line '- webhooks'
```

## Commands

- `merge --base B --ours O --theirs T` writes the merged text to standard output
  and a one-line summary to standard error. `--out FILE` writes the text to a
  file instead, `--json` prints a verdict document, `--quiet` drops the summary.
- `explain` takes the same inputs and prints the chunk table before the text.
- `--style diff3` writes the base section into each conflict, so a reader can see
  what each side changed *from* rather than only what they changed to.
- `--labels A,B` names the two sides in the markers.
- `demo` runs six merges with their claims checked; `selftest` re-checks the same
  answers without pytest.

```console
$ {{ npm_name }} merge --base base.txt --ours ours.txt --theirs theirs.txt --json
{
  "clean": true,
  "conflicts": 0,
  "agreed": 0,
  "chunks": 4,
  "changes": {
    "ours": 1,
    "theirs": 1
  },
  "text": "# changelog\n\n## 1.5.0\n- checkout\n- refunds\n- webhooks\n"
}
```

## Exit codes

| code | meaning |
|------|---------|
| 0 | merged, no conflict |
| 1 | merged, with conflict markers written |
| 2 | the merge could not be attempted: a missing file, an unknown style, a malformed label |

A conflict is not an error in the tool: the text was produced and it is exit 1
only so a script can tell the difference without parsing output.

## Layout

```
src/{{ package_name }}/
  change.py  a base text and an edited text become a list of edits
  merge.py   the chunks, the conflict markers, and the summary
  demo.py    six merges, each with its claim checked while it prints
  cli.py     merge / explain / demo / selftest
  selftest.py the same known answers, without pytest
tests/       edits, overlap rules, the merge, and the command line
fixtures/    a conflicted merge and a clean one, as files
```

## What this package does not do

- It is not a diff tool: `python-text-diff` is the stack for that.
- It does not merge trees, index files, or attention: it merges three texts.
- It does not resolve conflicts, and it never picks a side to avoid a marker. A
  merge that silently chooses is a merge that silently loses work.
