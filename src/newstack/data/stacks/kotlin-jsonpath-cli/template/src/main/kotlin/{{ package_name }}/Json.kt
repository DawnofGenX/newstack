package {{ package_name }}

// kotlin-jsonpath-cli

sealed class JsonValue {
    data class Obj(val value: LinkedHashMap<String, JsonValue>) : JsonValue()
    data class Arr(val value: ArrayList<JsonValue>) : JsonValue()
    data class Str(val value: String) : JsonValue()
    data class Num(val value: Double) : JsonValue()
    data class Bool(val value: Boolean) : JsonValue()
    object Null : JsonValue()

    fun toJson(): String = when (this) {
        is Obj -> value.entries.joinToString(",", "{", "}") { (k, v) -> "\"" + escape(k) + "\":" + v.toJson() }
        is Arr -> value.joinToString(",", "[", "]") { it.toJson() }
        is Str -> "\"" + escape(value) + "\""
        is Num -> if (value == value.toLong().toDouble() && !value.isNaN() && !value.isInfinite()) value.toLong().toString() else value.toString()
        is Bool -> value.toString()
        Null -> "null"
    }

    private fun escape(s: String): String {
        val sb = StringBuilder()
        for (c in s) {
            when (c) {
                '"' -> sb.append("\\\"")
                '\\' -> sb.append("\\\\")
                '\n' -> sb.append("\\n")
                '\r' -> sb.append("\\r")
                '\t' -> sb.append("\\t")
                else -> if (c.code < 0x20) sb.append("\\u%04x".format(c.code)) else sb.append(c)
            }
        }
        return sb.toString()
    }
}

object Json {
    fun parse(text: String): JsonValue {
        val p = Parser(text.trim())
        val v = p.parseValue()
        p.skipWs()
        if (p.pos != text.trim().length) throw IllegalArgumentException("trailing garbage at ${p.pos}")
        return v
    }

    private class Parser(val s: String) {
        var pos = 0
        fun skipWs() { while (pos < s.length && s[pos].isWhitespace()) pos++ }
        fun parseValue(): JsonValue {
            skipWs()
            if (pos >= s.length) throw IllegalArgumentException("unexpected end")
            return when (s[pos]) {
                '{' -> parseObj()
                '[' -> parseArr()
                '"' -> JsonValue.Str(parseString())
                't' -> { expect("true"); JsonValue.Bool(true) }
                'f' -> { expect("false"); JsonValue.Bool(false) }
                'n' -> { expect("null"); JsonValue.Null }
                else -> parseNumber()
            }
        }
        private fun expect(lit: String) {
            if (!s.startsWith(lit, pos)) throw IllegalArgumentException("expected $lit")
            pos += lit.length
        }
        private fun parseString(): String {
            if (s[pos] != '"') throw IllegalArgumentException("expected string")
            pos++
            val sb = StringBuilder()
            while (pos < s.length) {
                val c = s[pos++]
                if (c == '"') return sb.toString()
                if (c == '\\') {
                    if (pos >= s.length) throw IllegalArgumentException("bad escape")
                    val e = s[pos++]
                    when (e) {
                        '"' -> sb.append('"'); '\\' -> sb.append('\\'); '/' -> sb.append('/')
                        'n' -> sb.append('\n'); 'r' -> sb.append('\r'); 't' -> sb.append('\t')
                        'b' -> sb.append('\b'); 'f' -> sb.append('\u000c')
                        'u' -> {
                            val hex = s.substring(pos, pos + 4)
                            sb.append(hex.toInt(16).toChar())
                            pos += 4
                        }
                        else -> throw IllegalArgumentException("bad escape $e")
                    }
                } else sb.append(c)
            }
            throw IllegalArgumentException("unterminated string")
        }
        private fun parseNumber(): JsonValue {
            val start = pos
            while (pos < s.length && (s[pos].isDigit() || s[pos] == '-' || s[pos] == '+' || s[pos] == '.' || s[pos] == 'e' || s[pos] == 'E')) pos++
            val num = s.substring(start, pos).toDoubleOrNull() ?: throw IllegalArgumentException("bad number")
            return JsonValue.Num(num)
        }
        private fun parseObj(): JsonValue {
            pos++ // {
            skipWs()
            val m = linkedMapOf<String, JsonValue>()
            if (pos < s.length && s[pos] == '}') { pos++; return JsonValue.Obj(m) }
            while (true) {
                skipWs()
                val key = parseString()
                skipWs()
                if (pos >= s.length || s[pos] != ':') throw IllegalArgumentException("expected :")
                pos++
                val v = parseValue()
                m[key] = v
                skipWs()
                if (pos >= s.length) throw IllegalArgumentException("expected }")
                if (s[pos] == ',') { pos++; continue }
                if (s[pos] == '}') { pos++; break }
                throw IllegalArgumentException("expected , or }")
            }
            return JsonValue.Obj(m)
        }
        private fun parseArr(): JsonValue {
            pos++ // [
            skipWs()
            val a = arrayListOf<JsonValue>()
            if (pos < s.length && s[pos] == ']') { pos++; return JsonValue.Arr(a) }
            while (true) {
                val v = parseValue()
                a.add(v)
                skipWs()
                if (pos >= s.length) throw IllegalArgumentException("expected ]")
                if (s[pos] == ',') { pos++; continue }
                if (s[pos] == ']') { pos++; break }
                throw IllegalArgumentException("expected , or ]")
            }
            return JsonValue.Arr(a)
        }
    }
}
