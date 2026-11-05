# {{ title }}

{{ description }}

An R service built on [plumber](https://www.rplumber.io): annotated routes, a
pure contract function the tests drive without a socket, and no package
manager of its own — base R plus plumber is the whole stack.

## Run it

```sh
sudo apt-get install -y r-cran-plumber   # or: install.packages("plumber")
PORT=8080 Rscript bin/serve.R
```

```sh
curl 'http://127.0.0.1:8080/stats?text=hello%20world%0A'
# {"text":"hello world\n","lines":1,"words":2,"bytes":12}
```

## Endpoints

| request | answer |
| --- | --- |
| `GET /health` | `{"status":"ok"}` |
| `GET /stats?text=…` | `{"text", "lines", "words", "bytes"}`; a missing `text` → 422 `missing_text`, an empty one is a valid empty text |
| `POST /stats` with `{"text": "…"}` | the same body; missing or non-string `text` → 422 `missing_text`, a body that is not JSON → 422 `invalid_json` |
| nothing else | unknown path → 404 `not_found` with a `detail` naming the method and path; a known path with another method → 405 from plumber itself |

## Counting rules

* **line** — every `\n` byte, so a file ending in a newline has no extra empty line.
* **word** — every maximal run of non-space bytes (`isspace` is `' '`, `\t`, `\n`,
  `\r`, `\v`, `\f`).
* **byte** — the length of the UTF-8 encoding, not the number of characters:
  `"héllo wörld\n"` is 14 bytes in 12 characters.

The text is counted exactly as sent: `"  padded  \n"` is 11 bytes and one word,
even though it looks empty.

## Layout

```
plumber.R           the route table; plumber reads these annotations
R/counts.R          counting rules, no I/O
R/contract.R        the whole contract as one pure function: textstat_route(method, path, query, body)
bin/serve.R         reads PORT and HOST, installs the JSON 404 handler, starts the server
tests/run.R         the runner: sources the harness, the library and every *_test.R
tests/harness.R     a 40-line base-R assertion harness — no testthat, no network
tests/counts_test.R counting cases, including the UTF-8 ones
tests/contract_test.R every status code and body the service can answer
```

`bin/serve.R` also sets two things plumber does not default to:

* `serializer_unboxed_json()` — the default serializer writes every element of a
  list as a one-element array (`{"lines":[2]}`), which would break every client.
* `pr_set_parsers(app, c("form", "text", "octet"))` — with the JSON parser
  enabled plumber answers 500 to a malformed body before the handler runs; the
  contract wants 422 `invalid_json`, so the body is left alone and parsed by
  `textstat_route()`.

`req$QUERY_STRING` arrives with its `?` still attached, which is why
`textstat_query_param()` strips it.

## Test

```sh
Rscript tests/run.R
```
