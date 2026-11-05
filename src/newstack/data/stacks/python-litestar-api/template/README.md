# {{ title }}

{{ description }}

Requires Python {{ python_version }} or newer.

A text-statistics API on Litestar 2: `GET /health`, `GET /stats?text=…`,
`POST /stats` with `{"text": …}`. The rules live in
`src/{{ package_name }}/contract.py` as `route(method, target, body) -> (status, JSON)`,
so every status code can be asserted without a socket; `app.py` is the only file that
imports Litestar.

## Run

```bash
uv venv --allow-existing && uv pip install -e . pytest httpx ruff
PORT=8080 .venv/bin/python -m {{ package_name }}
curl -sS 'http://127.0.0.1:8080/stats?text=a+b'
```

## Check

```bash
.venv/bin/python -m {{ package_name }} --selftest   # 47 checks, no socket
.venv/bin/python -m pytest                         # pure contract + TestClient
.venv/bin/ruff check .
bash smoke.sh                                      # a real server on port 5464
```

## Traps this starter already paid for

- Litestar validates declared handler parameters *before* the handler runs and answers
  `400` with its own envelope. A `text: str` parameter would turn `missing_text` into
  "Expected `str`", so the handler takes `Request` and does the reading itself.
- `request.scope["raw_path"]` already ends with `?query`; appending
  `request.scope["query_string"]` as well makes `GET /stats?text=a+b` count
  `"a b?text=a b"`. The adapter appends the query only when `raw_path` lacks one.
- Litestar answers `HEAD` for a `GET` route itself, with the GET body's length and no
  body. The catch-all claims every method, so `HEAD /health` reaches the contract and
  answers `405` like every other stack in this family.
- `raw_path` is still percent-encoded and `request.url.path` is the normalised
  alternative; the `404` detail has to print what the client sent, so the raw form is
  what gets decoded byte-wise here.
- `Litestar(app_object)` served through `uvicorn.run(app)` keeps one app instance;
  passing the import string `"{{ package_name }}.app:app"` imports a second copy.
- The wheel is built from `src/{{ package_name }}`; without
  `[tool.hatch.build.targets.wheel] packages`, `pip install -e .` succeeds and
  `python -m {{ package_name }}` then fails with `No module named {{ package_name }}`.

## Layout

```
src/{{ package_name }}/counts.py     wc semantics over the bytes that arrived
src/{{ package_name }}/jsonread.py   found / missing / invalid for the `text` member
src/{{ package_name }}/contract.py   routes, status codes, percent decoding; no Litestar
src/{{ package_name }}/app.py        one catch-all route, raw target, raw body
src/{{ package_name }}/main.py       PORT/HOST, --selftest
src/{{ package_name }}/selftest.py   the offline checks
tests/test_contract.py               the rules, no framework
tests/test_app.py                    the same rules through Litestar's TestClient
smoke.sh                             starts the service, asserts every route with curl
```

Generated with [newstack](https://github.com/DawnofGenX/newstack).
