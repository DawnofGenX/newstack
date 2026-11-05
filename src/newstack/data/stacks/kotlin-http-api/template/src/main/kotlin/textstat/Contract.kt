package textstat

/**
 * Pure routing/contract layer. No sockets, no framework types.
 * Input: method + raw request target (path[?query], exactly as sent).
 * Output: status + response JSON as raw bytes.
 */
object Contract {

    data class Resp(val status: Int, val body: ByteArray)

    private val UTF8 = Charsets.ISO_8859_1 // bodies are assembled byte-exact already

    fun handle(method: String, target: String): Resp {
        val q = target.indexOf('?')
        val path = if (q >= 0) target.substring(0, q) else target
        val query = if (q >= 0) target.substring(q + 1) else null
        return when (path) {
            "/health" ->
                if (method == "GET") Resp(200, """{"status":"ok"}""".toBytesUtf8())
                else methodNotAllowed()
            "/stats" -> when (method) {
                "GET" -> statsGet(query)
                "POST" -> statsPost() // body supplied via handlePost
                else -> methodNotAllowed()
            }
            else -> notFound(method, target)
        }
    }

    /** POST /stats with raw body bytes. */
    fun handlePost(body: ByteArray): Resp = statsPostBody(body)

    private fun statsGet(query: String?): Resp {
        val raw = firstParam(query, "text") ?: return Resp(422, """{"error":"missing_text"}""".toBytesUtf8())
        val bytes = percentDecode(raw) ?: return Resp(422, """{"error":"missing_text"}""".toBytesUtf8())
        return statsOk(bytes)
    }

    private fun statsPost(): Resp = Resp(422, """{"error":"missing_text"}""".toBytesUtf8())
    private fun statsPostBody(body: ByteArray): Resp = when (val r = Json.readText(body)) {
        is Json.TextResult.Found -> statsOk(Json.bytesOf(r.text))
        Json.TextResult.Missing -> Resp(422, """{"error":"missing_text"}""".toBytesUtf8())
        is Json.TextResult.Invalid -> Resp(422, """{"error":"invalid_json"}""".toBytesUtf8())
    }

    private fun statsOk(bytes: ByteArray): Resp {
        val view = Json.view(bytes)
        val json = "{\"text\":\"${Json.escape(view)}\"," +
            "\"lines\":${Counts.lines(bytes)}," +
            "\"words\":${Counts.words(bytes)}," +
            "\"bytes\":${bytes.size}}"
        return Resp(200, json.toByteArray(UTF8))
    }

    private fun methodNotAllowed(): Resp = Resp(405, """{"error":"method_not_allowed"}""".toBytesUtf8())
    private fun notFound(method: String, target: String): Resp =
        Resp(404, "{\"error\":\"not_found\",\"detail\":\"no route for $method $target\"}".toBytesUtf8())

    /** first occurrence of `name` wins; value keeps raw (still percent-encoded) form */
    fun firstParam(query: String?, name: String): String? {
        if (query.isNullOrEmpty()) return null
        for (pair in query.split('&')) {
            val eq = pair.indexOf('=')
            val k = if (eq >= 0) pair.substring(0, eq) else pair
            if (k == name) return if (eq >= 0) pair.substring(eq + 1) else ""
        }
        return null
    }

    /** '+' -> space; %XX -> byte. Bad escapes -> null (caller: 422 missing_text). */
    fun percentDecode(raw: String): ByteArray? {
        val out = ArrayList<Byte>(raw.length)
        var i = 0
        while (i < raw.length) {
            val c = raw[i].code
            when {
                c == '+'.code -> { out.add(0x20); i++ }
                c == '%'.code -> {
                    if (i + 3 > raw.length) return null
                    val hi = hex(raw[i + 1]); val lo = hex(raw[i + 2])
                    if (hi < 0 || lo < 0) return null
                    out.add((hi * 16 + lo).toByte()); i += 3
                }
                c < 0x80 -> { out.add(c.toByte()); i++ }
                else -> return null // non-ASCII raw byte in query: reject
            }
        }
        return out.toByteArray()
    }

    private fun hex(c: Char): Int = when (c) {
        in '0'..'9' -> c - '0'
        in 'a'..'f' -> c - 'a' + 10
        in 'A'..'F' -> c - 'A' + 10
        else -> -1
    }

    private fun String.toBytesUtf8(): ByteArray = toByteArray(Charsets.ISO_8859_1)
}
