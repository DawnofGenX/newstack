# Lua HTTP API

A JSON service on LuaSocket. The counting, the route table and the HTTP
plumbing are three small modules with no framework and no LuaRocks install: the
interpreter, `socket` and `cjson` are the whole stack, and the tests never open
a socket.

## Endpoints

| Route | Answer |
| --- | --- |
| `GET /health` | `{"status":"ok"}` |
| `GET /stats?text=...` | `{"text":...,"lines":n,"words":n,"bytes":n}`, `422 missing_text` without `text` |
| `POST /stats` with `{"text":"..."}` | the same document, `422 invalid_json` for a body that is not JSON, `422 missing_text` for a body with no string `text` |
| any other method on `/health` or `/stats` | `405 method_not_allowed` |
| anything else | `404` with `{"error":"not_found","detail":"no route for METHOD /path"}` |

Counting is done over the bytes: a line is a `\n`, a word is a maximal run of
non-space bytes, and the byte count is the length of the string, which in Lua
*is* its byte count. `"héllo wörld\n"` is one line, two words and 14 bytes.

The response documents are written by hand instead of going through
`cjson.encode`, because Lua tables have no key order and the contract promises
one. `cjson` is only used to *read* a posted body, where it keeps `42` at `42`
and `"42"` at `"42"` — which is why `{"text": 42}` is a `422` and
`{"text": "42"}` is counted.

## Layout

| Path | What is in it |
| --- | --- |
| `src/counts.lua` | `count_text(text)` — one pass over the bytes, no regex engine |
| `src/contract.lua` | `route(method, path, query, body)` — a status and a JSON document out |
| `src/server.lua` | the socket half: read one request, call `route`, write one response |
| `bin/{{ npm_name }}` | the executable: resolves `src/` from its own path, binds the port |
| `tests/run.lua` | 26 checks, an assertion helper and nothing else |

## Run it

```sh
sudo apt-get install -y lua5.4 lua-socket lua-cjson
lua5.4 tests/run.lua
PORT=8080 ./bin/{{ npm_name }}
curl -sS 'http://127.0.0.1:8080/stats?text=hello%20world%0A'
```

The distribution's `lua-socket` and `lua-cjson` ship builds for each installed
Lua, so `lua5.4 -e 'require("socket")'` has to work before the service will
start; this template was proven on Lua 5.4.6 with LuaSocket 3.0.0 and cjson
2.1.0. `HOST` defaults to `127.0.0.1` and `PORT` to `8080`.
