# {{ title }}

An Erlang JSON service on [Cowboy](https://github.com/ninenines/cowboy), built with
rebar3 and released as an escript so there is exactly one process to start and one
process to stop.

    rebar3 escriptize
    rebar3 eunit
    PORT=8080 ./_build/default/bin/{{ npm_name }}

## Endpoints

| request | answer |
|---|---|
| `GET /health` | `{"status":"ok"}` |
| `GET /stats?text=...` | `{"text":...,"lines":1,"words":2,"bytes":12}` |
| `POST /stats` with `{"text": "..."}` | the same body for the posted text |
| `GET /stats` without `text` | `422 {"error":"missing_text"}` |
| `POST /stats` with a body that is not a JSON object | `422 {"error":"invalid_json"}` |
| a known path with another method | `405 {"error":"method_not_allowed"}` |
| anything else | `404 {"error":"not_found","detail":"no route for GET /nope"}` |

Counting follows `wc`: a line is a `"\n"` byte, a word is a maximal run of
non-space bytes, and bytes is the UTF-8 length - so `"héllo"` is five characters
and six bytes. The text is echoed back exactly as it arrived.

## Layout

| file | role |
|---|---|
| `src/counts.erl` | the counting rules, no I/O |
| `src/contract.erl` | the whole route table as a pure function: `route(Method, Path, Query, Body)` |
| `src/stat_handler.erl` | one Cowboy handler that forwards to `contract:route/4` |
| `src/{{ package_name }}_app.erl` | starts the listener on `PORT`, plus the supervisor |
| `src/{{ package_name }}.erl` | the escript entry point |
| `test/counts_tests.erl`, `test/contract_tests.erl` | eunit suites, no sockets |

The transport never decides a status code: `contract_tests.erl` pins every answer
without binding a port, and the CI job then exercises the same table over a real
socket.

`rebar.lock` is committed, so a fresh clone builds the exact cowboy/cowlib/ranch/jsx
versions this project was proven against.
