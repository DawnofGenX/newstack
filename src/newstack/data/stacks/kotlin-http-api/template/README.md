# {{ title }}

{{ description }}

Kotlin's standard library has no HTTP server, but the JDK does:
`Server.kt` hands every exchange to `com.sun.net.httpserver.HttpServer` and
`Contract.kt` turns it into a status code plus a JSON body. The counting core,
the JSON reader and the routes are pure Kotlin with no dependencies, and
`SelfTest.kt` is the whole suite — no JUnit, no test runner, just
`--selftest`.

## Layout

```
pom.xml                                 Maven build, shade -> target/{{ npm_name }}.jar
Makefile                                build / test / serve / clean
src/main/kotlin/textstat/Counts.kt      byte-exact wc counting
src/main/kotlin/textstat/Json.kt        JSON reader + escaper, surrogate pairs
src/main/kotlin/textstat/Contract.kt    routes, status codes, percent decoding
src/main/kotlin/textstat/Server.kt      the JDK HttpServer, nothing else
src/main/kotlin/textstat/Main.kt        --selftest, HOST/PORT, exit codes
src/main/kotlin/textstat/SelfTest.kt    50 checks, no framework
bin/{{ npm_name }}                           build once, then run the server
```

## Run

```sh
make test
PORT=8080 ./bin/{{ npm_name }}
curl -s 'http://127.0.0.1:8080/stats?text=hello%20world%0A'
```

## Traps this starter already paid for

- `HttpServer.create` needs an `InetSocketAddress`, and a bare
  `HttpServer.create()` does not exist — `Server.kt` builds the address from
  `HOST`/`PORT` so the service binds loopback by default.
- The JDK replies with its own `404`/`405` unless a context is registered for
  `/`; the root context is what lets the router decide status codes itself.
- Kotlin's `String` is UTF-16, so every byte count goes through the `ByteArray`
  (`text.toByteArray(Charsets.UTF_8).size`), never `text.length`.
- `\\uXXXX` escapes must be decoded to UTF-8 bytes, and a surrogate pair
  (`\\uD83D\\uDE00`) is one code point — decoding each half separately yields
  replacement characters.
- The shaded jar must name its main class in the shade transformer, otherwise
  `java -jar` fails with `no main manifest attribute`.
- Maven writes `dependency-reduced-pom.xml` next to the build; it is generated
  output and belongs in `.gitignore`.
