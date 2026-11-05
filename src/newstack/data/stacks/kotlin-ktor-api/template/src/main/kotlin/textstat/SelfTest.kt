package textstat

/**
 * Offline assertion suite: no socket, no Ktor engine. Asserts the exact
 * contract (Contract.kt) the server translates, so a green --selftest means
 * the routing/counting/decoding core is correct independent of transport.
 *
 * Exit code = number of failed checks (0 == all passed).
 */
object SelfTest {
    private class Report {
        var checks = 0
        val failures = mutableListOf<String>()

        inline fun check(label: String, block: () -> Boolean) {
            checks++
            val ok = try { block() } catch (e: Throwable) { false }
            if (!ok) failures += "  FAIL: $label"
        }
    }

    fun run(): Int {
        val r = Report()

        // ---- wc counting semantics (task fixtures first) ----
        r.check("fixture 'a b\\n' -> 1/2/4") {
            fixture("a b\n", 1, 2, 4)
        }
        r.check("fixture 'héllo wörld\\n' -> 1/2/14") {
            fixture("héllo wörld\n", 1, 2, 14)
        }
        r.check("fixture 'a b\\nc\\n' -> 2/3/6") {
            fixture("a b\nc\n", 2, 3, 6)
        }
        r.check("fixture '' -> 0/0/0") { fixture("", 0, 0, 0) }
        r.check("tabs/CR/VT/FF are separators") {
            fixture("a\u000Bb\u000Cc", 0, 3, 5)
        }
        r.check("multi-space run is one boundary") {
            fixture("a   b", 0, 2, 5)
        }
        r.check("leading/trailing separators do not add words") {
            fixture("  a  \n", 1, 1, 6)
        }
        r.check("3 newlines = 3 lines, 0 words") {
            fixture("\n\n\n", 3, 0, 3)
        }
        r.check("no trailing newline: 'a b\\nc' -> 1/3/5") {
            fixture("a b\nc", 1, 3, 5)
        }
        r.check("CJK is not split by separator logic") {
            fixture("你好 世界\n", 1, 2, 14)
        }
        r.check("byte count is UTF-8 not chars") {
            Counts.byteCount("é") == 2 && Counts.lines("é") == 0
        }

        // ---- query decoding: + is space, %XX is raw byte -> UTF-8 ----
        r.check("%C3%A9 -> é") { Contract.decodeComponent("%C3%A9") == "é" }
        r.check("café as caf%C3%A9") { Contract.decodeComponent("caf%C3%A9") == "café" }
        r.check("+ -> space") { Contract.decodeComponent("a+b") == "a b" }
        r.check("%20 -> space") { Contract.decodeComponent("a%20b") == "a b" }
        r.check("mixed é+space") { Contract.decodeComponent("caf%C3%A9+bar") == "café bar" }
        r.check("malformed %zz stays literal") { Contract.decodeComponent("%zz") == "%zz" }
        r.check("truncated %C3 stays literal") { Contract.decodeComponent("%C3") == "%C3" }
        r.check("literal % in value passes through") {
            Contract.decodeComponent("100%25") == "100%"
        }
        r.check("uppercase hex %41 -> A") { Contract.decodeComponent("%41") == "A" }
        r.check("4-byte emoji surrogate round trip") {
            Contract.decodeComponent("%F0%9F%98%80") == "😀"
        }

        // ---- query parameter rules ----
        r.check("first text wins") {
            Contract.parseTextParam("text=a+bb&text=zzz") == "a bb"
        }
        r.check("text after other params") {
            Contract.parseTextParam("x=1&text=hi") == "hi"
        }
        r.check("leading ? stripped by parseTextParam too") {
            Contract.parseTextParam("?text=hi") == "hi"
        }
        r.check("no text -> null") { Contract.parseTextParam("x=1") == null }
        r.check("null query -> null") { Contract.parseTextParam(null) == null }
        r.check("bare 'text' (no =) is empty value") {
            Contract.parseTextParam("text") == ""
        }
        r.check("text= empty value is empty string not null") {
            Contract.parseTextParam("text=") == ""
        }

        // ---- GET /stats end to end (contract level) ----
        r.check("GET stats missing text -> 422 missing_text") {
            val o = Contract.getStats("x=1")
            o.status == 422 && o.body == "{\"error\":\"missing_text\"}"
        }
        r.check("GET stats empty text -> 200 0/0/0") {
            val o = Contract.getStats("text=")
            o.status == 200 && o.body == "{\"text\":\"\",\"lines\":0,\"words\":0,\"bytes\":0}"
        }
        r.check("GET stats exact key order text,lines,words,bytes") {
            Contract.getStats("text=a+b")
                .body == "{\"text\":\"a b\",\"lines\":0,\"words\":2,\"bytes\":3}"
        }

        // ---- POST /stats body discrimination ----
        r.check("POST valid text") {
            val o = Contract.postStats("{\"text\":\"a b\\n\"}")
            o.status == 200 && o.body == "{\"text\":\"a b\\n\",\"lines\":1,\"words\":2,\"bytes\":4}"
        }
        r.check("POST no text member -> missing_text") {
            val o = Contract.postStats("{\"other\":1}")
            o.status == 422 && o.body == "{\"error\":\"missing_text\"}"
        }
        r.check("POST empty object -> missing_text") {
            Contract.postStats("{}").body == "{\"error\":\"missing_text\"}"
        }
        r.check("POST text:null -> invalid_json") {
            val o = Contract.postStats("{\"text\":null}")
            o.status == 422 && o.body == "{\"error\":\"invalid_json\"}"
        }
        r.check("POST text number -> invalid_json") {
            Contract.postStats("{\"text\":42}").body == "{\"error\":\"invalid_json\"}"
        }
        r.check("POST text array -> invalid_json") {
            Contract.postStats("{\"text\":[1]}").body == "{\"error\":\"invalid_json\"}"
        }
        r.check("malformed json -> invalid_json") {
            Contract.postStats("{\"text\":\"a\"").body == "{\"error\":\"invalid_json\"}"
        }
        r.check("trailing garbage -> invalid_json") {
            Contract.postStats("{\"text\":\"a\"} x").body == "{\"error\":\"invalid_json\"}"
        }
        r.check("empty body -> invalid_json") {
            Contract.postStats("").body == "{\"error\":\"invalid_json\"}"
        }
        r.check("POST duplicate text key: first wins") {
            Contract.postStats("{\"text\":\"one\",\"text\":\"two\"}")
                .body == "{\"text\":\"one\",\"lines\":0,\"words\":1,\"bytes\":3}"
        }
        r.check("POST extra members ignored") {
            Contract.postStats("{\"n\":9,\"text\":\"a\"}").status == 200
        }
        r.check("POST escaped unicode \\u00e9") {
            Contract.postStats("{\"text\":\"caf\\u00e9\"}").status == 200
        }

        // ---- route table ----
        r.check("GET /health 200") { Contract.statusFor("GET", "/health") == 200 }
        r.check("POST /health 405") { Contract.statusFor("POST", "/health") == 405 }
        r.check("GET /stats 200") { Contract.statusFor("GET", "/stats") == 200 }
        r.check("POST /stats 200") { Contract.statusFor("POST", "/stats") == 200 }
        r.check("PUT /stats 405") { Contract.statusFor("PUT", "/stats") == 405 }
        r.check("DELETE /stats 405") { Contract.statusFor("DELETE", "/stats") == 405 }
        r.check("unknown / 404") { Contract.statusFor("GET", "/") == 404 }
        r.check("unknown /nope 404") { Contract.statusFor("GET", "/nope") == 404 }
        r.check("trailing slash /health/ is unknown 404") {
            Contract.statusFor("GET", "/health/") == 404
        }
        r.check("health exact body") {
            Contract.dispatch("GET", "/health", null, null)
                .body == "{\"status\":\"ok\"}"
        }

        // ---- dispatch (what the interceptor calls verbatim) ----
        r.check("dispatch 405 body") {
            Contract.dispatch("POST", "/health", null, "")
                .body == "{\"error\":\"method_not_allowed\"}"
        }
        r.check("dispatch 404 detail, method uppercased") {
            Contract.dispatch("get", "/nope", "q=1", null)
                .body == "{\"error\":\"not_found\",\"detail\":\"no route for GET /nope\"}"
        }
        r.check("404 detail never carries a query string") {
            Contract.dispatch("GET", "/x", "text=y", null)
                .body == "{\"error\":\"not_found\",\"detail\":\"no route for GET /x\"}"
        }

        // ---- PORT resolution ----
        r.check("PORT unset -> 5472") { Contract.resolvePort(null) == 5472 }
        r.check("PORT 8080 honoured") { Contract.resolvePort("8080") == 8080 }
        r.check("PORT abc -> null (exit 2)") { Contract.resolvePort("abc") == null }
        r.check("PORT 0 out of range -> null") { Contract.resolvePort("0") == null }
        r.check("PORT 70000 -> null") { Contract.resolvePort("70000") == null }

        // ---- stack probe: kotlinx serializer really in the jar ----
        r.check("kotlinx serializer round trip") {
            Json.serializerProbeRoundTrip() == "{\"text\":\"ok\",\"value\":7}"
        }

        // ---- report ----
        for (f in r.failures) println(f)
        println("selftest: ${r.checks} checks passed")
        return r.failures.size
    }

    private fun fixture(text: String, lines: Int, words: Int, bytes: Int): Boolean =
        Counts.lines(text) == lines && Counts.words(text) == words &&
            Counts.byteCount(text) == bytes
}
