# {{ title }}

A small `wc`-shaped counter whose real subject is the plumbing around it: what the
exit code means, what happens when the reader hangs up, and why a count measured in
the wrong unit is worse than no count.

```
$ printf 'one two three\nfour\n' > notes.txt
$ {{ npm_name }} notes.txt
lines words bytes notes.txt
    2     4    19 notes.txt
$ printf 'one two\n' | {{ npm_name }} --json
{
  "files": [
    {
      "path": "-",
      "lines": 1,
      "words": 2,
      "bytes": 8
    }
  ],
  "total": {
    "lines": 1,
    "words": 2,
    "bytes": 8
  }
}
```

## Quick start

```bash
npm install
npm run build
node dist/src/{{ package_name }}/main.js README.md
npm test
bash smoke.sh
```

| Code | Meaning |
| --- | --- |
| `0` | everything was read and counted |
| `1` | a file could not be read, or `--fail-empty` found no lines |
| `2` | the command line was wrong |

## The traps this template exists to expose

1. **`chunk.toString()` is not decoding.** A UTF-8 character split across two reads
   becomes two replacement characters; `bytes` stays right while `words` quietly grows.
   `new TextDecoder("utf-8")` with `{stream: true}` keeps the partial sequence.
2. **`/\S+/g` per chunk splits words.** A word straddling a buffer boundary counts
   twice, so the same file gives different numbers depending on read sizes — the worst
   kind of bug, because both answers look plausible. The trailing word is carried.
3. **`wc -l` counts newlines, not lines.** `a\nb` is two lines to every editor and one
   to `wc`. This tool counts logical lines and says so; a test pins `a\nb` to 2.
4. **`.length` on a string is characters, not bytes.** `"héllo"` is 5 characters and
   6 bytes; only the buffer knows. The column is labelled `bytes` for a reason.
5. **CRLF.** A Windows checkout must not double the line count, and `\r` must not
   become a word of its own.
6. **EPIPE is not a crash.** `prog | head -1` closes stdout under a running process.
   Node turns that into an unhandled `'error'` event, a stack trace and exit 1 — so a
   perfectly normal pipeline reports failure. Handled explicitly, exit 0, no noise.
7. **A misspelled flag must not be ignored.** `--jsn` silently rendering a table is
   how a pipeline ends up parsing human output for weeks. Unknown options exit 2.
8. **Zero is not "could not read".** A file that failed is shown as `?` with its
   `ENOENT`, never as a row of zeros that reads like an empty file.
9. **A terminal is not an empty pipe.** With no operands and a TTY, reading stdin
   blocks forever with no prompt; that is exit 2 with a sentence instead.

## Layout

```
src/{{ package_name }}/count.ts   streaming counter: streaming decode, carried word, logical lines
src/{{ package_name }}/format.ts  right-aligned table and the JSON report
src/{{ package_name }}/cli.ts     argument parser, exit codes, file and stdin reads
src/{{ package_name }}/main.ts    the EPIPE handler, and nothing else
tests/                            node:test, including the pipeline case through a real child process
smoke.sh                          the contract end to end: exit codes, pipes, multibyte bytes
```
