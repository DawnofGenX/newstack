package textstat

/**
 * The wire contract, framework-free, so --selftest can assert it without a socket.
 * Server.kt is a thin translation layer over exactly these decisions.
 */
object Contract {
    const val DEFAULT_PORT = 5472
    const val HEALTH_BODY = "{\"status\":\"ok\"}"

    class Outcome(val status: Int, val body: String)

    const val OK = 200
    const val NOT_FOUND = 404
    const val METHOD_NOT_ALLOWED = 405
    const val UNPROCESSABLE = 422

    /** Route table, consulted by both the server and the offline suite. */
    fun statusFor(method: String, path: String): Int = when (path) {
        "/health" -> if (method == "GET") OK else METHOD_NOT_ALLOWED
        "/stats" -> if (method == "GET" || method == "POST") OK else METHOD_NOT_ALLOWED
        else -> NOT_FOUND
    }

    fun getHealth(): Outcome = Outcome(OK, HEALTH_BODY)

    fun getStats(rawQuery: String?): Outcome {
        val text = parseTextParam(rawQuery) ?: return Outcome(UNPROCESSABLE, Json.MISSING_TEXT)
        return statsOf(text)
    }

    fun postStats(body: String): Outcome = when (val extracted = Json.extractText(body)) {
        is Json.Body.Text -> statsOf(extracted.value)
        Json.Body.Missing -> Outcome(UNPROCESSABLE, Json.MISSING_TEXT)
        Json.Body.Invalid -> Outcome(UNPROCESSABLE, Json.INVALID_JSON)
    }

    private fun statsOf(text: String): Outcome = Outcome(
        OK,
        Json.stats(text, Counts.lines(text), Counts.words(text), Counts.byteCount(text))
    )

    fun dispatch(method: String, path: String, rawQuery: String?, body: String?): Outcome =
        when (statusFor(method, path)) {
            OK -> when {
                path == "/health" -> getHealth()
                method == "GET" -> getStats(rawQuery)
                else -> postStats(body ?: "")
            }
            METHOD_NOT_ALLOWED -> Outcome(METHOD_NOT_ALLOWED, Json.methodNotAllowed())
            else -> Outcome(
                NOT_FOUND,
                Json.notFound(method.uppercase(), path.ifEmpty { "/" })
            )
        }

    /** First `text` param wins; no `text` param -> null (-> 422 missing_text). */
    fun parseTextParam(rawQuery: String?): String? {
        if (rawQuery.isNullOrEmpty()) return null
        val query = rawQuery.removePrefix("?")
        for (part in query.split('&')) {
            val eq = part.indexOf('=')
            val rawKey = if (eq < 0) part else part.substring(0, eq)
            if (decodeComponent(rawKey) == "text") {
                return decodeComponent(if (eq < 0) "" else part.substring(eq + 1))
            }
        }
        return null
    }

    /**
     * `+` -> space; `%XX` -> raw byte, accumulated bytes interpreted as UTF-8;
     * other characters pass through and contribute their own UTF-8 bytes.
     * A malformed escape (`%zz`) or truncated sequence (`%C3`) that leaves
     * invalid UTF-8 degrades to the literal input, matching the
     * permissive-decoder behaviour callers expect from query strings.
     */
    fun decodeComponent(raw: String): String {
        val out = java.io.ByteArrayOutputStream(raw.length)
        var i = 0
        var literal = false
        while (i < raw.length) {
            val c = raw[i]
            when {
                c == '+' -> { out.write(0x20); i++ }
                c == '%' && i + 2 < raw.length &&
                    isHex(raw[i + 1]) && isHex(raw[i + 2]) -> {
                    out.write(hex(raw[i + 1]) * 16 + hex(raw[i + 2]))
                    i += 3
                }
                c == '%' -> {
                    // malformed escape (%zz, trailing %): force the literal fallback below
                    literal = true
                    i++
                }
                else -> {
                    for (b in c.toString().toByteArray(Charsets.UTF_8)) out.write(b.toInt())
                    i++
                }
            }
        }
        if (literal) return raw
        val bytes = out.toByteArray()
        return try {
            java.nio.charset.StandardCharsets.UTF_8
                .newDecoder()
                .onMalformedInput(java.nio.charset.CodingErrorAction.REPORT)
                .onUnmappableCharacter(java.nio.charset.CodingErrorAction.REPORT)
                .decode(java.nio.ByteBuffer.wrap(bytes)).toString()
        } catch (e: java.nio.charset.CharacterCodingException) {
            raw // truncated multibyte escape: keep the value literal
        }
    }

    private fun isHex(c: Char): Boolean =
        c in '0'..'9' || c in 'a'..'f' || c in 'A'..'F'

    private fun hex(c: Char): Int = when (c) {
        in '0'..'9' -> c - '0'
        in 'a'..'f' -> c - 'a' + 10
        else -> c - 'A' + 10
    }

    /** PORT env resolution: non-numeric (or out of range) -> null, caller exits 2. */
    fun resolvePort(envValue: String?, fallback: Int = DEFAULT_PORT): Int? {
        if (envValue.isNullOrBlank()) return fallback
        val trimmed = envValue.trim()
        val port = trimmed.toIntOrNull() ?: return null
        return if (port in 1..65535) port else null
    }
}
