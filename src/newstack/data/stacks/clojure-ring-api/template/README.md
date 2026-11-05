# {{ title }}

A JSON service in Clojure with Ring and Jetty, on `deps.edn` — no Leiningen, no framework.

The interesting part is what the handler is: a plain function from a Ring request map to a
response map. `ring.mock.request` builds those maps, so the suite exercises every route without
opening a port, and `server.clj` is the only file that knows a port exists.

## Requirements

- Java 21+ (`java -version`)
- The Clojure CLI 1.12+ (`clojure -Sdescribe`)
- `curl`, for the smoke test

Maven dependencies download on the first run into `~/.m2`.

## Layout

```
deps.edn                   dependencies and the :test alias
src/{{ package_name }}/counts.clj   counting rules, no HTTP
src/{{ package_name }}/handler.clj  handler: a request map in, a response map out
src/{{ package_name }}/server.clj   Jetty, PORT, -main
test/{{ package_name }}/counts_test.clj
test/{{ package_name }}/handler_test.clj
test/{{ package_name }}/run_tests.clj       the non-interactive runner
```

## Run it

```sh
clojure -M:test -m {{ package_name }}.run-tests
PORT=8080 clojure -M -m {{ package_name }}.server

curl 'http://127.0.0.1:8080/health'
curl 'http://127.0.0.1:8080/stats?text=hello%20world%0A'
curl -X POST -H 'content-type: application/json' \
     --data-binary '{"text":"a b\nc\n"}' http://127.0.0.1:8080/stats
```

`GET /stats` returns the counted text plus `lines`, `words` and `bytes`. A missing `text`
parameter is a `422`, an unparseable body is a `422` (never a `500`), an unknown path is a JSON
`404`, and a method the route does not implement is a `405`.

Counting matches `wc`: a line ends at `\n`, a word is a maximal run of non-space characters,
`bytes` is the UTF-8 length — `héllo` is 5 characters and 6 bytes, which is why the counting
uses `(.getBytes text "UTF-8")` rather than `count`.

## Test it

```sh
clojure -M:test -m {{ package_name }}.run-tests
```

`run_tests.clj` requires the test namespaces, runs `clojure.test/run-tests` and exits non-zero
when anything fails, so a shell (or CI) can trust the process status. `clojure.test` is built
in; the only test-only dependency is `ring/ring-mock`, which lives in the `:test` alias so the
production classpath stays clean.

## Notes

- `ring/ring-jetty-adapter` is the server; `ring/ring-core` gives `ring.util.codec` for query
  parsing. `cheshire` encodes and decodes JSON.
- The template ships no lock file. `deps.edn` pins exact `:mvn/version`s, so resolution is
  reproducible without one; `clojure -Stree` shows the tree.
