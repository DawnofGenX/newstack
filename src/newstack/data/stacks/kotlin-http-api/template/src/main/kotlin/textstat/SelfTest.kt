package textstat

/**
 * In-process check harness: prints "ok <name>" / "FAIL <name>".
 * Returns true if everything passed. 34 checks over Counts/Json/Contract.
 */
object SelfTest {
    private var pass = 0
    private var fail = 0

    private fun check(name: String, cond: Boolean) {
        if (cond) { pass++; println("ok $name") }
        else { fail++; println("FAIL $name") }
    }

    private fun b(s: String) = s.toByteArray(Charsets.ISO_8859_1) // byte-view helper
    private fun utf(s: String) = s.toByteArray(Charsets.UTF_8)
    private fun resp(m: String, t: String) = Contract.handle(m, t)
    private fun post(body: String) = Contract.handlePost(b(body))
    private fun bodyOf(r: Contract.Resp) = String(r.body, Charsets.ISO_8859_1)

    fun run(): Boolean {
        pass = 0; fail = 0

        // ---- counting (wc-style, raw bytes) ----
        val hello = utf("héllo wörld\n")
        check("count-hello-lines", Counts.lines(hello) == 1)
        check("count-hello-words", Counts.words(hello) == 2)
        check("count-hello-bytes", Counts.bytes(hello) == 14)
        check("count-empty", Counts.bytes(b("")) == 0 && Counts.words(b("")) == 0 && Counts.lines(b("")) == 0)
        check("count-newline-only", Counts.lines(b("\n\n")) == 2 && Counts.words(b("\n\n")) == 0)
        check("count-delims", Counts.words(b(" \t\n\r\u000B\u000C ")) == 0)
        check("count-run-of-word", Counts.words(b("abc")) == 1)
        check("count-vtab-breaks-word", Counts.words(b("a\u000Bb")) == 2)
        check("count-utf8-word-1", Counts.words(utf("café")) == 1)
        check("count-utf8-bytes", Counts.bytes(utf("café")) == 5)

        // ---- JSON reader ----
        check("json-valid-simple", runCatching { Json.parse(b("""{"a":1}""")) }.isSuccess)
        check("json-trailing-garbage-rejected",
            runCatching { Json.parse(b("""{"a":1} oops""")) }.isFailure)
        check("json-empty-rejected", runCatching { Json.parse(b("")) }.isFailure)
        check("json-text-simple",
            Json.readText(b("""{"text":"hi"}""")) == Json.TextResult.Found("hi"))
        check("json-text-last-wins",
            Json.readText(b("""{"text":"a","x":1,"text":"b"}""")) == Json.TextResult.Found("b"))
        check("json-text-nested-skipped-but-scanned",
            Json.readText(b("""{"n":{"m":{"text":"deep"}}}""")) == Json.TextResult.Found("deep"))
        check("json-text-nonstring-42-missing",
            Json.readText(b("""{"text":42}""")) == Json.TextResult.Missing)
        check("json-text-empty-obj-missing",
            Json.readText(b("{}")) == Json.TextResult.Missing)
        check("json-text-arrays-scanned",
            Json.readText(b("""[{"text":"one"},{"text":"two"}]""")) == Json.TextResult.Found("two"))
        check("json-unicode-escape-cafe",
            Json.readText(b("{\"text\":\"caf\\u00e9\"}")) ==
                Json.TextResult.Found(Json.view(utf("café"))))
        check("json-surrogate-pair-emoji",
            Json.readText(b("""{"text":"\uD83D\uDE00"}""")) ==
                Json.TextResult.Found(Json.view(utf("\uD83D\uDE00"))))
        check("json-lone-surrogate-rejected",
            Json.readText(b("""{"text":"\uD83D"}""")) is Json.TextResult.Invalid)
        check("json-array-trailing-garbage",
            bodyOf(post("""{"text":"x"}]""")).contains("invalid_json"))
        check("json-control-char-rejected",
            bodyOf(post("""{"text":"a	b"}""")).contains("invalid_json"))

        // ---- escape / echo ----
        check("escape-quotes", Json.escape("""a"b\c""") == """a\"b\\c""")
        check("escape-controls", Json.escape("\n\r\t\b\u000C") == "\\n\\r\\t\\b\\f")
        check("escape-low-ctrl-u", Json.escape("\u0001") == "\\u0001")
        check("escape-utf8-passthrough",
            Json.escape(Json.view(utf("é"))) == Json.view(utf("é")))

        // ---- percent decoding ----
        check("pct-plus-is-space", Contract.percentDecode("a+b") contentEquals b("a b"))
        check("pct-hex", Contract.percentDecode("a%20b") contentEquals b("a b"))
        check("pct-utf8-bytes", Contract.percentDecode("%C3%A9") contentEquals utf("é"))
        check("pct-bad-hex-null", Contract.percentDecode("%ZZ") == null)
        check("pct-truncated-null", Contract.percentDecode("%4") == null)

        // ---- query param ----
        check("query-first-wins", Contract.firstParam("text=1&text=2", "text") == "1")
        check("query-missing-null", Contract.firstParam("a=1", "text") == null)

        // ---- contract routes ----
        check("health-200", resp("GET", "/health").let { it.status == 200 && bodyOf(it) == """{"status":"ok"}""" })
        check("health-post-405", resp("POST", "/health").let { it.status == 405 && bodyOf(it) == """{"error":"method_not_allowed"}""" })
        check("health-delete-405", resp("DELETE", "/health").status == 405)
        check("stats-put-405", resp("PUT", "/stats").status == 405)
        check("stats-get-hello",
            resp("GET", "/stats?text=hello%20world%0A").let {
                it.status == 200 && bodyOf(it) == """{"text":"hello world\n","lines":1,"words":2,"bytes":12}"""
            })
        check("stats-get-utf8",
            resp("GET", "/stats?text=h%C3%A9llo%20w%C3%B6rld%0A").let {
                it.status == 200 && bodyOf(it) ==
                    "{\"text\":\"h" + Json.view(utf("é")) + "llo w" + Json.view(utf("ö")) + "rld\\n\",\"lines\":1,\"words\":2,\"bytes\":14}"
            })
        check("stats-get-empty-text-ok",
            resp("GET", "/stats?text=").let {
                it.status == 200 && bodyOf(it) == """{"text":"","lines":0,"words":0,"bytes":0}"""
            })
        check("stats-get-no-param-422",
            resp("GET", "/stats").let { it.status == 422 && bodyOf(it) == """{"error":"missing_text"}""" })
        check("stats-get-other-param-only-422",
            resp("GET", "/stats?data=x").status == 422)
        check("stats-post-missing-422",
            post("{}").let { it.status == 422 && bodyOf(it) == """{"error":"missing_text"}""" })
        check("stats-post-nonstring-422",
            post("""{"text":42}""").let { it.status == 422 && bodyOf(it) == """{"error":"missing_text"}""" })
        check("stats-post-invalid-422",
            post("{oops").let { it.status == 422 && bodyOf(it) == """{"error":"invalid_json"}""" })
        check("404-detail",
            resp("GET", "/nope?x=1").let {
                it.status == 404 && bodyOf(it) == """{"error":"not_found","detail":"no route for GET /nope?x=1"}"""
            })
        check("404-unknown-method-known-path-missing",
            resp("HEAD", "/stats").status == 405)
        check("404-root-any-method",
            resp("GET", "/").let { it.status == 404 && bodyOf(it).endsWith("GET /\"}") })

        println("-- $pass passed, $fail failed")
        return fail == 0
    }
}
