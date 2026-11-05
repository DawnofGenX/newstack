package textstat

/**
 * Minimal strict JSON reader over RAW UTF-8 bytes + JSON string escaper.
 *
 * INTERNAL REPRESENTATION TRAP: decoded string values are held as a
 * "byte-view" String — one Char (0x00..0xFF) per RAW UTF-8 byte, never
 * decoded to codepoints. This keeps counting and echoing byte-exact for
 * arbitrary UTF-8 (Kotlin Strings are UTF-16; decoding then re-encoding
 * risks loss for exotic sequences and always costs a round-trip).
 * Escape decoding emits UTF-8 BYTES into the byte-view too.
 *
 * Reader rules (contract):
 *  - reject trailing garbage after the top-level value
 *  - reject control chars in strings, comments, single quotes, trailing commas
 *  - \uXXXX decodes incl. surrogate pairs (re-encoded to UTF-8 bytes)
 *  - readText: LAST member named "text" whose value is a STRING wins,
 *    at any depth (nested objects/arrays are scanned then skipped)
 */
object Json {

    class JsonInvalid(msg: String) : Exception(msg)

    sealed class TextResult {
        data class Found(val text: String) : TextResult()      // byte-view text
        object Missing : TextResult()                          // valid JSON, no string "text"
        data class Invalid(val why: String) : TextResult()     // not valid JSON
    }

    sealed class Value {
        object Null : Value()
        data class Bool(val v: Boolean) : Value()
        data class Num(val byteView: String) : Value()
        data class Str(val byteView: String) : Value()
        data class Arr(val items: List<Value>) : Value()
        data class Obj(val members: List<Pair<String, Value>>) : Value() // key = byte-view
    }

    private class Reader(private val src: ByteArray) {
        private var i = 0
        private fun peek(): Int = if (i < src.size) src[i].toInt() and 0xFF else -1
        private fun eof(): Boolean = i >= src.size
        private fun skipWs() {
            while (!eof()) {
                val c = src[i].toInt() and 0xFF
                if (c == 0x20 || c == 0x09 || c == 0x0A || c == 0x0D) i++ else break
            }
        }
        private fun expect(ch: Int) {
            if (eof() || (src[i].toInt() and 0xFF) != ch) throw JsonInvalid("expected '${ch.toChar()}' at byte $i")
            i++
        }
        private fun literal(word: String) {
            for (c in word) {
                if (eof() || (src[i].toInt() and 0xFF) != c.code) throw JsonInvalid("bad literal near byte $i")
                i++
            }
        }

        fun value(): Value {
            skipWs()
            if (eof()) throw JsonInvalid("empty input")
            return when (val c = peek()) {
                '{'.code -> obj()
                '['.code -> arr()
                '"'.code -> Value.Str(string())
                't'.code -> { literal("true"); Value.Bool(true) }
                'f'.code -> { literal("false"); Value.Bool(false) }
                'n'.code -> { literal("null"); Value.Null }
                else -> if (c == '-'.code || c in '0'.code..'9'.code) number()
                        else throw JsonInvalid("unexpected byte 0x${c.toString(16)} at $i")
            }
        }

        private fun obj(): Value.Obj {
            expect('{'.code)
            val out = ArrayList<Pair<String, Value>>()
            skipWs()
            if (peek() == '}'.code) { i++; return Value.Obj(out) }
            while (true) {
                skipWs()
                if (eof() || peek() != '"'.code) throw JsonInvalid("expected string key at byte $i")
                val k = string()
                skipWs(); expect(':'.code)
                out.add(k to value())
                skipWs()
                when (peek()) {
                    ','.code -> { i++; continue }
                    '}'.code -> { i++; return Value.Obj(out) }
                    else -> throw JsonInvalid("expected ',' or '}' at byte $i")
                }
            }
        }

        private fun arr(): Value.Arr {
            expect('['.code)
            val out = ArrayList<Value>()
            while (true) {
                out.add(value())
                skipWs()
                when (peek()) {
                    ','.code -> { i++; continue }
                    ']'.code -> { i++; return Value.Arr(out) }
                    else -> throw JsonInvalid("expected ',' or ']' at byte $i")
                }
            }
        }

        private fun number(): Value.Num {
            val start = i
            if (peek() == '-'.code) i++
            while (!eof()) {
                val c = src[i].toInt() and 0xFF
                if (c in '0'.code..'9'.code || c == 'e'.code || c == 'E'.code ||
                    c == '+'.code || c == '.'.code || c == '-'.code) i++ else break
            }
            val s = String(src, start, i - start, Charsets.ISO_8859_1)
            if (s.isEmpty() || s == "-") throw JsonInvalid("bad number at byte $start")
            return Value.Num(s)
        }

        /** returns byte-view String (one Char per raw UTF-8 byte) */
        private fun string(): String {
            expect('"'.code)
            val sb = StringBuilder()
            while (true) {
                if (eof()) throw JsonInvalid("unterminated string")
                val c = src[i].toInt() and 0xFF
                when {
                    c == '"'.code -> { i++; return sb.toString() }
                    c == '\\'.code -> { i++; escape(sb) }
                    c < 0x20 -> throw JsonInvalid("control char 0x${c.toString(16)} in string at $i")
                    else -> {
                        val len = utf8Len(c)
                        if (i + len > src.size) throw JsonInvalid("truncated UTF-8 at $i")
                        repeat(len) { sb.append((src[i + it].toInt() and 0xFF).toChar()) }
                        i += len
                    }
                }
            }
        }

        private fun escape(sb: StringBuilder) {
            if (eof()) throw JsonInvalid("dangling escape")
            val c = src[i].toInt() and 0xFF
            i++
            when (c) {
                '"'.code -> sb.append('"')
                '\\'.code -> sb.append('\\')
                '/'.code -> sb.append('/')
                'b'.code -> sb.append('\u0008')
                'f'.code -> sb.append('\u000C')
                'n'.code -> sb.append('\u000A')
                'r'.code -> sb.append('\u000D')
                't'.code -> sb.append('\u0009')
                'u'.code -> unicode(sb)
                else -> throw JsonInvalid("bad escape backslash-${c.toChar()} at $i")
            }
        }

        private fun unicode(sb: StringBuilder) {
            var cp = hex4()
            if (cp in 0xD800..0xDBFF) {
                if (i + 1 < src.size && (src[i].toInt() and 0xFF) == '\\'.code &&
                    (src[i + 1].toInt() and 0xFF) == 'u'.code) {
                    i += 2
                    val lo = hex4()
                    if (lo !in 0xDC00..0xDFFF) throw JsonInvalid("lone high surrogate")
                    cp = 0x10000 + ((cp - 0xD800) shl 10) + (lo - 0xDC00)
                } else throw JsonInvalid("unpaired high surrogate")
            } else if (cp in 0xDC00..0xDFFF) throw JsonInvalid("lone low surrogate")
            // emit as UTF-8 bytes into the byte-view
            for (b in cp.toUtf8Bytes()) sb.append((b.toInt() and 0xFF).toChar())
        }

        private fun hex4(): Int {
            if (i + 4 > src.size) throw JsonInvalid("truncated \\u escape")
            var v = 0
            repeat(4) {
                val c = src[i + it].toInt() and 0xFF
                val d = when {
                    c in '0'.code..'9'.code -> c - '0'.code
                    c in 'a'.code..'f'.code -> c - 'a'.code + 10
                    c in 'A'.code..'F'.code -> c - 'A'.code + 10
                    else -> throw JsonInvalid("bad hex in \\u escape")
                }
                v = v * 16 + d
            }
            i += 4
            return v
        }

        fun finish() {
            skipWs()
            if (!eof()) throw JsonInvalid("trailing garbage at byte $i")
        }
    }

    private fun utf8Len(b0: Int): Int = when {
        b0 < 0x80 -> 1
        b0 and 0xE0 == 0xC0 -> 2
        b0 and 0xF0 == 0xE0 -> 3
        b0 and 0xF8 == 0xF0 -> 4
        else -> throw JsonInvalid("bad UTF-8 lead byte 0x${b0.toString(16)}")
    }

    private fun Int.toUtf8Bytes(): ByteArray = when {
        this < 0x80 -> byteArrayOf(toByte())
        this < 0x800 -> byteArrayOf(
            (0xC0 or (this shr 6)).toByte(),
            (0x80 or (this and 0x3F)).toByte()
        )
        this < 0x10000 -> byteArrayOf(
            (0xE0 or (this shr 12)).toByte(),
            (0x80 or ((this shr 6) and 0x3F)).toByte(),
            (0x80 or (this and 0x3F)).toByte()
        )
        else -> byteArrayOf(
            (0xF0 or (this shr 18)).toByte(),
            (0x80 or ((this shr 12) and 0x3F)).toByte(),
            (0x80 or ((this shr 6) and 0x3F)).toByte(),
            (0x80 or (this and 0x3F)).toByte()
        )
    }

    /** Strict parse of the whole document. Throws JsonInvalid on any violation. */
    fun parse(body: ByteArray): Value {
        val r = Reader(body)
        val v = r.value()
        r.finish()
        return v
    }

    /** LAST object member named "text" with a STRING value, any depth. Byte-view result. */
    fun readText(body: ByteArray): TextResult {
        val v = try { parse(body) } catch (e: JsonInvalid) { return TextResult.Invalid(e.message ?: "invalid") }
        var last: String? = null
        fun scan(x: Value) {
            when (x) {
                is Value.Obj -> for ((k, sub) in x.members) {
                    if (k == "text" && sub is Value.Str) last = sub.byteView
                    scan(sub)
                }
                is Value.Arr -> x.items.forEach { scan(it) }
                else -> {}
            }
        }
        scan(v)
        return last?.let { TextResult.Found(it) as TextResult } ?: TextResult.Missing
    }

    // ---------------- writer ----------------

    /** byte-view String -> raw UTF-8 bytes */
    fun bytesOf(byteView: String): ByteArray {
        val out = ByteArray(byteView.length)
        for (k in byteView.indices) out[k] = byteView[k].code.toByte()
        return out
    }

    /** raw UTF-8 bytes -> byte-view String */
    fun view(bytes: ByteArray): String {
        val sb = StringBuilder(bytes.size)
        for (b in bytes) sb.append((b.toInt() and 0xFF).toChar())
        return sb.toString()
    }

    /**
     * Escape a byte-view String for JSON output. Input bytes >=0x80 pass
     * through untouched (UTF-8 passthrough); the caller writes the result
     * with writeAscii/ISO-88591 so bytes land verbatim on the wire.
     */
    fun escape(byteView: String): String {
        val sb = StringBuilder(byteView.length + 8)
        for (c in byteView) {
            val v = c.code
            when (v) {
                '"'.code -> sb.append("\\\"")
                '\\'.code -> sb.append("\\\\")
                '\n'.code -> sb.append("\\n")
                '\r'.code -> sb.append("\\r")
                '\t'.code -> sb.append("\\t")
                0x08 -> sb.append("\\b")
                0x0C -> sb.append("\\f")
                else -> if (v < 0x20) sb.append("\\u%04x".format(v)) else sb.append(c)
            }
        }
        return sb.toString()
    }
}
