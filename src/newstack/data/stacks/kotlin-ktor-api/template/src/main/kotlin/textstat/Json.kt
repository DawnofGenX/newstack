package textstat

/**
 * Hand-rolled JSON for the wire contract.
 *
 * Reasons this is not delegated to kotlinx.serialization on the hot path:
 *  - the response key order must be exactly text,lines,words,bytes / error,detail
 *    with zero whitespace, and error payloads must never gain fields;
 *  - request discrimination needs three outcomes (missing text / non-string
 *    text / malformed JSON) which map to two distinct 422 bodies, so the
 *    parser has to know where the document stopped.
 *
 * kotlinx.serialization is still on the classpath (the stack probe) and is
 * exercised by Json.kt's own serializer round-trip below.
 */
object Json {
    const val MISSING_TEXT = "{\"error\":\"missing_text\"}"
    const val INVALID_JSON = "{\"error\":\"invalid_json\"}"
    const val NOT_FOUND_PREFIX = "{\"error\":\"not_found\",\"detail\":\"no route for "

    fun escaped(s: String): String = buildString(s.length + 8) {
        for (c in s) when (c) {
            '"' -> append("\\\"")
            '\\' -> append("\\\\")
            '\n' -> append("\\n")
            '\r' -> append("\\r")
            '\t' -> append("\\t")
            '\b' -> append("\\b")
            '' -> append("\\f")
            else -> if (c < ' ') append("\\u%04x".format(c.code)) else append(c)
        }
    }

    fun stats(text: String, lines: Int, words: Int, bytes: Int): String =
        "{\"text\":\"${escaped(text)}\",\"lines\":$lines,\"words\":$words,\"bytes\":$bytes}"

    fun methodNotAllowed(): String = "{\"error\":\"method_not_allowed\"}"
    fun notFound(method: String, path: String): String =
        NOT_FOUND_PREFIX + escaped(method + " " + path) + "\"}"

    /** Scanned-but-not-a-string scalar (number/bool/null), kept opaque to callers. */
    internal class NonString(val raw: String)

    /** Probe that the kotlinx serializer really in the jar. */
    fun serializerProbeRoundTrip(): String {
        val original = kotlinx.serialization.json.Json { explicitNulls = false }
        return original.encodeToString(
            ProbePayload.serializer(),
            ProbePayload(text = "ok", value = 7)
        )
    }

    sealed class Body {
        data class Text(val value: String) : Body()
        data object Missing : Body()
        data object Invalid : Body()
    }

    private class ParseError : RuntimeException()

    fun extractText(source: String): Body {
        val p = Parser(source)
        return try {
            p.skipWs()
            if (p.peek() != '{') throw ParseError()
            p.next()
            var text: Body = Body.Missing
            p.skipWs()
            if (p.peek() == '}') {
                p.next()
            } else {
                while (true) {
                    p.skipWs()
                    val key = p.string()
                    p.skipWs()
                    if (p.next() != ':') throw ParseError()
                    p.skipWs()
                    if (key == "text") {
                        val v = p.value()
                        if (v !is String) {
                            throw ParseError()
                        } else {
                            if (text !is Body.Text) text = Body.Text(v) // first wins
                        }
                    } else {
                        p.value()
                    }
                    p.skipWs()
                    when (val c = p.next()) {
                        ',' -> continue
                        '}' -> break
                        else -> throw ParseError()
                    }
                }
            }
            p.skipWs()
            if (!p.atEnd) throw ParseError()
            text
        } catch (e: ParseError) {
            Body.Invalid
        } catch (e: NoSuchElementException) {
            Body.Invalid
        }
    }

    /** Strict-enough scanner; throws ParseError the moment the document stops being JSON. */
    private class Parser(private val s: String) {
        private var i = 0
        val atEnd: Boolean get() = i >= s.length

        fun peek(): Char {
            if (i >= s.length) throw ParseError()
            return s[i]
        }

        fun next(): Char {
            if (i >= s.length) throw ParseError()
            return s[i++]
        }

        fun skipWs() {
            while (i < s.length && s[i].let { it == ' ' || it == '\t' || it == '\n' || it == '\r' }) i++
        }

        fun string(): String {
            if (next() != '"') throw ParseError()
            return buildString {
                while (true) {
                    when (val c = next()) {
                        '"' -> return toString()
                        '\\' -> append(escape())
                        else -> append(c)
                    }
                }
            }
        }

        private fun escape(): Char = when (val e = next()) {
            '"', '\\', '/' -> e
            'b' -> '\b'
            'f' -> ''
            'n' -> '\n'
            'r' -> '\r'
            't' -> '\t'
            'u' -> {
                var v = 0
                repeat(4) {
                    val d = Character.digit(next(), 16)
                    if (d < 0) throw ParseError()
                    v = v * 16 + d
                }
                v.toInt().toChar()
            }
            else -> throw ParseError()
        }

        /** Returns String for strings, otherwise an opaque marker for the scanned value. */
        fun value(): Any {
            return when (peek()) {
                '"' -> string()
                '{' -> { next(); obj(); Unit }
                '[' -> { next(); arr(); Unit }
                else -> literal()
            }
        }

        private fun obj() {
            skipWs()
            if (peek() == '}') { next(); return }
            while (true) {
                skipWs(); string(); skipWs()
                if (next() != ':') throw ParseError()
                skipWs(); value()
                skipWs()
                when (next()) {
                    ',' -> continue
                    '}' -> return
                    else -> throw ParseError()
                }
            }
        }

        private fun arr() {
            skipWs()
            if (peek() == ']') { next(); return }
            while (true) {
                skipWs(); value()
                skipWs()
                when (next()) {
                    ',' -> continue
                    ']' -> return
                    else -> throw ParseError()
                }
            }
        }

        private fun literal(): Any {
            val start = i
            while (i < s.length && (s[i].isLetterOrDigit() || s[i] in "+-.eE")) i++
            val tok = s.substring(start, i)
            return when {
                tok == "true" || tok == "false" || tok == "null" -> NonString(tok)
                tok.toDoubleOrNull() != null -> NonString(tok)
                else -> throw ParseError()
            }
        }
    }
}

@kotlinx.serialization.Serializable
internal data class ProbePayload(val text: String, val value: Int)
