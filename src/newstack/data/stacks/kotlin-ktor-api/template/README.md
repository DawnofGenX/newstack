# {{ npm_name }}

Text-statistics HTTP probe proving a **Ktor 3 + kotlinx.serialization + JDK 21 +
Maven** stack builds to one runnable shaded jar and serves an exact wire
contract. No framework beyond Ktor server itself.

## Contract

| Request | Response |
| --- | --- |
| `GET /health` | `200 {"status":"ok"}` |
| `GET /stats?text=...` | `200 {"text":"...","lines":N,"words":N,"bytes":N}` |
| `GET /stats` (no `text`) | `422 {"error":"missing_text"}` |
| `POST /stats` `{"text":"..."}` | `200 {"text":"...","lines":N,"words":N,"bytes":N}` |
| `POST /stats` without `text` member | `422 {"error":"missing_text"}` |
| `POST /stats` non-string `text` / malformed JSON | `422 {"error":"invalid_json"}` |
| wrong method on `/health` or `/stats` | `405 {"error":"method_not_allowed"}` |
| unknown path | `404 {"error":"not_found","detail":"no route for <METHOD> <PATH>"}` |

Response key order is exactly `text,lines,words,bytes` (errors:
`error[,detail]`), compact, UTF-8. Query decoding: `+` is a space, `%XX` is a
raw byte then interpreted as UTF-8, the first `text` parameter wins, a leading
`?` is not part of the value.

Counting is `wc(1)` over raw UTF-8 bytes: **lines** = `0x0A` count, **words** =
maximal runs outside `{0x20,0x09,0x0A,0x0D,0x0B,0x0C}`, **bytes** = UTF-8
length. Fixtures: `"a b\n"`→1/2/4, `"héllo wörld\n"`→1/2/14, `"a b\nc\n"`→2/3/6,
`""`→0/0/0.

Server binds `127.0.0.1:5472`; `PORT` env overrides it; a non-numeric `PORT`
exits `2`.

## Layout

```
pom.xml                        artifactId {{ npm_name }}, finalName {{ npm_name }},
                               kotlin-maven-plugin 2.2.21 + maven-shade-plugin
                               (mainClass textstat.MainKt), release 21
bin/{{ npm_name }}                 wrapper: java -jar target/{{ npm_name }}.jar "$@"
smoke.sh                       live curl assertions against :5472
src/main/kotlin/textstat/
  Counts.kt                    wc semantics over UTF-8 bytes
  Json.kt                      exact-order writer + strict request parser
  Contract.kt                  route table, query decoder, PORT rule — no Ktor
  Server.kt                    Ktor 3 Setup-phase interception -> Contract
  Main.kt                      --selftest | serve
  SelfTest.kt                  62 offline assertions, no socket
src/test/kotlin/textstat/
  ContractTest.kt              16 JUnit 5 tests over a real socket, ephemeral port
```

## Commands

```
make build      # mvn -q -B -DskipTests package -> target/{{ npm_name }}.jar
make test       # mvn -q -B test (ContractTest, real socket)
make selftest   # java -jar target/{{ npm_name }}.jar --selftest
make serve      # serve on 127.0.0.1:5472 (PORT overrides)
bash smoke.sh   # boots the jar, asserts the contract, and returns the port on EXIT
```

## Traps this starter already paid for

1. **Ktor 3.x `Application` *is* the pipeline.** `application.pipeline` is gone;
   you call `intercept(ApplicationCallPipeline.Setup) { ... }` directly on the
   `Application` receiver, and the call is `this.context` (or the `call`
   extension from `io.ktor.server.application.call`), not `this.call`.
2. **The interceptor lambda is `suspend`,** so `receiveText()`/`respondText()`
   work inside it — but *not* inside non-suspend helpers you pull out of it;
   mark helpers `suspend` or inline them.
3. **`intercept` is a Pipeline member, not a top-level function** — the old
   `io.ktor.util.pipeline.intercept` import path no longer resolves; there is
   no `PipelineKt` to import from in ktor-utils 3.x.
4. **No `rawQuery` on `ApplicationRequest`.** Properties live on
   `io.ktor.server.request.*` (`uri`, `path()`, `httpMethod`); strip the query
   from `request.uri` yourself after the path is taken with `path()`.
5. **`embeddedServer(...)` returns `EmbeddedServer<TEngine, TConf>`, not
   `ApplicationEngine`** — annotating the helper's return type as
   `ApplicationEngine` fails compilation; let inference carry it.
6. **Ktor's own 404/405 bodies break byte-exact contracts.** Routing answers
   unknown paths itself, so raw interception on `Setup` + `finish()` after
   `respondText` is what keeps `{"error":"not_found","detail":"no route for ..."}`
   verbatim (and makes `/health/` a 404, not a rewrite).
7. **kotlinx `Json` silently accepts `"text":42` and `"text":null`** when you
   only need to check string-ness — the 422 discrimination
   (`missing_text` vs `invalid_json`) needs a parser that knows the document
   position; hence the hand-rolled strict scanner in `Json.kt` (kotlinx stays
   installed + probe-checked so the plugin/serializer stack is still proven).
8. **UTF-8 query decoding is byte-level, not char-level:** `%C3` alone must not
   produce U+FFFD; decode accumulated bytes through a `CharsetDecoder` in
   `REPORT` mode and fall back to the literal on `CharacterCodingException`.
9. **Shading Ktor needs `ServicesResourceTransformer`** (Ktor discovers engine
   factories via `META-INF/services`) and netty `module-info`/signature
   exclusion, or the fat jar runs in the IDE but dies under `java -jar`.
10. **Maven Kotlin plugin needs the `kotlinx-serialization` compiler plugin
    wired into `kotlin-maven-plugin` itself** (the `kotlin-maven-serialization`
    dependency) — `@Serializable` code in `Json.kt` compiles to nothing useful
    without it.

11. **A step's trap must wait for the JVM.** `kill` only signals, so a step that kills the
    server and exits can leave the listener closing while the next step starts; the trap here
    sends `TERM`, polls for up to two seconds, escalates to `KILL`, and then `wait`s.
12. **`dependency-reduced-pom.xml` is generated, not authored.** `maven-shade-plugin` rewrites
    the pom next to it on every package run; it belongs in `.gitignore`, never in the template.
