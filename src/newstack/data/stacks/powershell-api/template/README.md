# {{ title }}

{{ description }}

A PowerShell 7 JSON service on `System.Net.HttpListener` that counts lines,
words and bytes the way `wc` does. Everything that decides a status code lives
in `src/Textstat.psm1` (`Invoke-TextstatRoute` is a pure function of method,
path, query and body), so `tests/run.ps1` pins the whole route table without
opening a port; `src/server.ps1` is the only file that touches a socket.

## Endpoints

| Method | Path | Answer |
| --- | --- | --- |
| `GET` | `/health` | `200 {"status":"ok"}` |
| `GET` | `/stats?text=...` | `200 {"text","lines","words","bytes"}`, `422 {"error":"missing_text"}` when `text` is absent |
| `POST` | `/stats` with `{"text": "..."}` | same body as `GET`; `422 {"error":"missing_text"}` for a non-string `text`, `422 {"error":"invalid_json"}` for a body that is not one JSON object |
| any | a known path with another method | `405 {"error":"method_not_allowed"}` |
| any | anything else | `404 {"error":"not_found","detail":"no route for METHOD /path"}` |

The text is counted exactly as sent: `"  padded  \n"` is one line, one word and
eleven bytes, and a trailing newline is a line of its own.

## Running it

```sh
pwsh -NoProfile -File tests/run.ps1
PORT=8080 pwsh -NoProfile -File src/server.ps1
curl 'http://127.0.0.1:8080/stats?text=hello%20world%0A'
```

`ConvertFrom-Json` keeps the string/number distinction, so `{"text": 42}` is
rejected with `422 missing_text` while `{"text": "42"}` is counted; the
`PSObject.Properties['text']` lookup is what tells an absent field from a null.
