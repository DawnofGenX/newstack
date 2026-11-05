# {{ project_name }}

A JSON service in C++17 with nothing but the standard library and POSIX
sockets: no CMake, no third-party JSON library, one `make`.

```console
$ make
c++ -Iinclude -D_POSIX_C_SOURCE=200809L -std=c++17 -O2 -g -Wall -Wextra -Wpedantic -Werror -c -o build/counts.o src/counts.cpp
...
$ make test
checks: 47, passed: 47, failed: 0

$ PORT=8080 ./build/{{ npm_name }}
listening on http://127.0.0.1:8080
```

## What it counts

`textstat::count(std::string_view)` — a line is one `'\n'`, a word is a maximal
run of non-space bytes (space, tab, newline, carriage return, `\v`, `\f`), and
bytes are the raw length of the buffer. Nothing is decoded, so `"héllo wörld\n"`
is 1 line, 2 words and 14 bytes.

## Routes

| Method | Path | Answer |
| --- | --- | --- |
| `GET` | `/health` | `{"status":"ok"}` |
| `GET` | `/stats?text=…` | `{"text":…,"lines":…,"words":…,"bytes":…}` |
| `POST` | `/stats` | the same shape, from a `{"text":"…"}` JSON body |

A body that is not JSON is `422 invalid_json`; a body without a *string* `text`
member is `422 missing_text`, so `{"text":42}` is rejected while
`{"text":"42"}` is counted. A known path under another method is `405`, and
anything else is a JSON `404` naming method and path.

## Layout

| File | Role |
| --- | --- |
| `include/textstat/counts.hpp`, `src/counts.cpp` | the counter, byte at a time |
| `include/textstat/json.hpp`, `src/json.cpp` | a validating JSON reader that remembers whether `text` was a string |
| `include/textstat/contract.hpp`, `src/contract.cpp` | `route` — pure, no sockets |
| `include/textstat/http.hpp`, `src/http.cpp` | one request per connection on a POSIX socket |
| `src/main.cpp` | reads `HOST` and `PORT` |
| `tests/` | a hand-rolled check harness, run by `make test` |

The JSON reader validates the whole document — trailing data is an error — and
keeps a JSON number apart from a JSON string, which is why `{"text":42}` and
`{"text":"42"}` answer differently.
