# {{ project_name }}

A JSON service in Groovy on the plain distribution: `com.sun.net.httpserver`
from the JDK, `JsonSlurper` from Groovy's own runtime, and no Gradle, no JUnit,
no jar to resolve.

```console
$ groovy -cp src tests/RunTests.groovy
checks: 37, passed: 37, failed: 0

$ PORT=8080 ./bin/{{ npm_name }}
listening on http://127.0.0.1:8080
```

## What it counts

Same rules as `wc`: a line is one `'\n'`, a word is a maximal run of non-space
bytes, and bytes are UTF-8 — which matters in Groovy, because a `String` is
UTF-16 in memory and `length()` would count characters. The counting core
therefore walks the UTF-8 bytes, so `"héllo wörld\n"` is 1 line, 2 words and 14
bytes.

## Routes

| Method | Path | Answer |
| --- | --- | --- |
| `GET` | `/health` | `{"status":"ok"}` |
| `GET` | `/stats?text=…` | `{"text":…,"lines":…,"words":…,"bytes":…}` |
| `POST` | `/stats` | the same shape, from a `{"text":"…"}` JSON body |

A missing or non-string `text` is `422 missing_text`; a body that is not a JSON
object is `422 invalid_json`. Because `JsonSlurper` already keeps a JSON string
as a `String` and a JSON number as a `BigDecimal`, `{"text": 42}` is
`missing_text` while `{"text": "42"}` is counted. A known path under another
method is `405`, and anything else is a JSON `404` naming method and path.

## Layout

| File | Role |
| --- | --- |
| `src/textstat/Counts.groovy` | `Counts.of` — counting over UTF-8 bytes, no I/O |
| `src/textstat/Json.groovy` | `Json.readText` — `INVALID`, `MISSING` or `TEXT` |
| `src/textstat/Reply.groovy` | status plus body, one small value class |
| `src/textstat/Contract.groovy` | `route` — pure: method/path/query/body in, reply out |
| `src/textstat/Server.groovy` | the `HttpServer` adapter, single threaded |
| `src/textstat/App.groovy` | reads `HOST`/`PORT` and blocks |
| `tests/RunTests.groovy` | a plain script of named checks, no test framework |

There is no compile step: `groovy -cp src` compiles what it needs and runs it,
so the test script is the gate and the server starts the same way.
