# {{ project_name }}

A JSON service in Java 21 on `com.sun.net.httpserver` — that class lives in the
JDK, so there is no framework and no dependency to download. `make` and `javac`
are the whole build.

```console
$ make
$ make test
checks: 33, passed: 33, failed: 0

$ PORT=8080 java -cp build/classes {{ package_name }}.App
listening on http://127.0.0.1:8080
```

## What it counts

Same rules as `wc`: a line is one `'\n'`, a word is a maximal run of non-space
characters (space, tab, newline, carriage return, vertical tab and form feed all
separate), and bytes are the UTF-8 encoding — so `"héllo wörld\n"` is 1 line, 2
words and 14 bytes. Text is counted exactly as it arrives: nothing is trimmed.

## Routes

| Method | Path | Answer |
| --- | --- | --- |
| `GET` | `/health` | `{"status":"ok"}` |
| `GET` | `/stats?text=…` | `{"text":…,"lines":…,"words":…,"bytes":…}` |
| `POST` | `/stats` | the same shape, from a `{"text":"…"}` JSON body |

A missing or non-string `text` is `422 missing_text`; a body that is not a JSON
object is `422 invalid_json`; a known path with another method is `405
method_not_allowed`; anything else is `404 not_found` with a `detail`.

## Layout

```
Makefile                                   javac -Xlint:all -Werror, then the checks
src/main/java/{{ package_name }}/Counts.java      the three numbers, no HTTP in sight
src/main/java/{{ package_name }}/JsonBody.java    the JSON reader: string vs number
src/main/java/{{ package_name }}/Contract.java    method + path + query + body → reply
src/main/java/{{ package_name }}/Server.java      the JDK HTTP server, one handler
src/main/java/{{ package_name }}/App.java         entry point, HOST and PORT env vars
tests/RunTests.java                        33 checks, no test framework
```

The contract is a pure function of four strings, so the suite covers every status
code without opening a socket; `make` on its own proves the project builds with
every javac warning promoted to an error.
