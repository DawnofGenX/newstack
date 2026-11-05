# {{ title }}

{{ description }}

Octave has no sockets of its own, but it ships a JVM bridge: `serve.m` opens a
`java.net.ServerSocket`, reads the request head one byte at a time through the
Java `InputStream` and answers with `route/3`, which is pure Octave. `counts.m`
counts over the raw `uint8` bytes, `jsonread.m` is a recursive-descent reader
that keeps only the `text` member, and `selftest.m` is the whole suite — no
packages, no toolbox.

## Layout

```
main.m                   addpath, TEXTSTAT_SELFTEST, PORT/HOST
lib/serve.m              java.net.ServerSocket loop
lib/handle_client.m      head byte-by-byte, Content-Length body, response writer
lib/route.m              routes, percent decoding, JSON writer
lib/jsonread.m           JSON object reader (last text member wins)
lib/skip_value.m         nested values, depth cap
lib/parse_string.m       escapes and UTF-8 encoding of code points
lib/counts.m             lines / words / bytes over raw bytes
lib/selftest.m           27 checks, no framework
tests/run_tests.m        the suite as a script with an exit status
bin/{{ npm_name }}             run the server, or --selftest
```

## Run

```sh
octave --no-window-system --quiet tests/run_tests.m
PORT=8080 ./bin/{{ npm_name }}
curl -s 'http://127.0.0.1:8080/stats?text=hello%20world%0A'
```

## Traps this starter already paid for

- Octave passes structs **by value**. A helper that walks a buffer cannot mutate
  the caller's cursor: it must take `st` in and return it, and every caller must
  write `[st, ok] = helper(raw, st)`. Forgetting one return silently rewinds the
  parser to where it started.
- An Octave function with several outputs returns only the FIRST when called
  with one output — `counts(raw)` is the line count, not a triple. Unpack it:
  `[lines, words, nbytes] = counts(raw)`.
- `counts.m` indexes a 256-entry separator table by byte value, so no `for` loop
  compares characters, and the file stays fast over multi-megabyte bodies.
- `strcmp` compares classes: a `uint8` vector never equals a `char` vector, even
  with the same bytes. Compare `char(percent_decode(key))` to the parameter name.
- The JVM bridge is available but not always started: `serve.m` needs
  `usejava('jvm')` to be true (it is on a normal package build; pass
  `--no-gui` so Octave does not try to open a window).
- `InputStream.read()` returns `-1` at end of stream and a plain number
  otherwise — accumulate `uint8(b)`, never `char`.
- Octave ignores `SIGTERM` while it is blocked inside Java's `accept()`. The
  workflow step therefore sends `SIGTERM`, waits up to two seconds, and then
  escalates to `SIGKILL`; a plain `kill` plus `wait` hangs until the CI timeout.
