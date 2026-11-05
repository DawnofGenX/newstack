# Guile HTTP API

A JSON service on the Guile web server. No framework, no JSON library of our
own: `(web server)` from Guile and `(json)` from guile-json, plus a route table
that is a plain procedure so the tests never open a socket.

## Endpoints

| Route | Answer |
| --- | --- |
| `GET /health` | `{"status":"ok"}` |
| `GET /stats?text=...` | `{"text":...,"lines":n,"words":n,"bytes":n}`, `422 missing_text` without `text` |
| `POST /stats` with `{"text":"..."}` | the same document, `422 invalid_json` for a body that is not JSON, `422 missing_text` for a body with no string `text` |
| any other method on `/health` or `/stats` | `405 method_not_allowed` |
| anything else | `404` with `{"error":"not_found","detail":"no route for METHOD /path"}` |

Counting is done over the UTF-8 bytes, so it agrees with `wc -c`: a line is a
`\n`, a word is a maximal run of non-space characters, and the byte count is
the length of the decoded payload. `"héllo wörld\n"` is one line, two words and
14 bytes.

## Layout

| Path | What is in it |
| --- | --- |
| `lib/textstat/counts.scm` | the counting record and the JSON document it renders |
| `lib/textstat/contract.scm` | `route` — method, path, query and body in, a status and a document out |
| `lib/textstat/server.scm` | the socket half: read the request, call `route`, write one document |
| `main.scm` | the executable: one call into the server module |
| `tests/` | a hand-rolled harness and two suites, 30 checks, no socket |

## Run it

```sh
sudo apt-get install -y guile-3.0 guile-json
env GUILE_AUTO_COMPILE=0 guile --no-auto-compile -L lib -L tests -s tests/run-tests.scm
PORT=8080 env GUILE_AUTO_COMPILE=0 guile --no-auto-compile -L lib main.scm
curl -sS 'http://127.0.0.1:8080/stats?text=hello%20world%0A'
```

`guile-json` is the one dependency, and it comes from the distribution:
`(use-modules (json))` is not part of Guile itself. The version this template
was proven on is guile-json 4.7.3 with Guile 3.0.9.
