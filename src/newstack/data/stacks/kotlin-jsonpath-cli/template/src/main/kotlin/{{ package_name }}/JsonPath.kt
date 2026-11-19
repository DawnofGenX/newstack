package {{ package_name }}

// kotlin-jsonpath-cli

object JsonPath {
    fun evaluate(path: String, root: JsonValue): List<JsonValue> {
        val p = path.trim()
        if (p == "$" || p.isEmpty()) return listOf(root)
        var cur: List<JsonValue> = listOf(root)
        var i = 0
        val s = if (p.startsWith("$")) p.substring(1) else p
        i = 0
        while (i < s.length) {
            when (s[i]) {
                '.' -> {
                    if (i + 1 < s.length && s[i + 1] == '.') {
                        // recursive descent
                        val name = readIdent(s, i + 2)
                        i += 2 + name.length
                        cur = recursive(cur, name)
                    } else {
                        i++
                        if (i >= s.length) break
                        if (s[i] == '*') { i++; cur = cur.flatMap { v -> children(v) } }
                        else {
                            val name = readIdent(s, i)
                            i += name.length
                            cur = cur.mapNotNull { v -> (v as? JsonValue.Obj)?.value?.get(name) }
                        }
                    }
                }
                '[' -> {
                    val end = s.indexOf(']', i)
                    if (end < 0) throw IllegalArgumentException("unterminated bracket")
                    val inner = s.substring(i + 1, end).trim()
                    i = end + 1
                    cur = applyBracket(cur, inner)
                }
                else -> {
                    // bare ident at start
                    val name = readIdent(s, i)
                    if (name.isEmpty()) throw IllegalArgumentException("bad path: $path")
                    i += name.length
                    cur = cur.mapNotNull { v -> (v as? JsonValue.Obj)?.value?.get(name) }
                }
            }
        }
        return cur
    }

    private fun readIdent(s: String, start: Int): String {
        val sb = StringBuilder()
        var i = start
        while (i < s.length && (s[i].isLetterOrDigit() || s[i] == '_' || s[i] == '-')) { sb.append(s[i]); i++ }
        return sb.toString()
    }

    private fun children(v: JsonValue): List<JsonValue> = when (v) {
        is JsonValue.Obj -> v.value.values.toList()
        is JsonValue.Arr -> v.value
        else -> emptyList()
    }

    private fun recursive(cur: List<JsonValue>, name: String): List<JsonValue> {
        val out = mutableListOf<JsonValue>()
        fun walk(v: JsonValue) {
            when (v) {
                is JsonValue.Obj -> {
                    v.value[name]?.let { out.add(it) }
                    v.value.values.forEach { walk(it) }
                }
                is JsonValue.Arr -> v.value.forEach { walk(it) }
                else -> {}
            }
        }
        cur.forEach { walk(it) }
        return out
    }

    private fun applyBracket(cur: List<JsonValue>, inner: String): List<JsonValue> {
        return when {
            inner == "*" -> cur.flatMap { v -> (v as? JsonValue.Arr)?.value ?: emptyList() }
            inner.startsWith("?") -> {
                val cond = inner.substring(1).trim().let { c -> if (c.startsWith("(") && c.endsWith(")")) c.substring(1, c.length - 1).trim() else c }
                cur.flatMap { v ->
                    val arr = (v as? JsonValue.Arr)?.value ?: return@flatMap emptyList()
                    arr.filter { elem -> evalFilter(cond, elem) }
                }
            }
            inner.startsWith("'") || inner.startsWith("\"") -> {
                val key = inner.trim('\'', '"')
                cur.mapNotNull { v -> (v as? JsonValue.Obj)?.value?.get(key) }
            }
            inner.contains(":") -> {
                val parts = inner.split(":")
                val start = parts.getOrNull(0)?.trim()?.toIntOrNull() ?: 0
                val end = parts.getOrNull(1)?.trim()?.toIntOrNull()
                cur.flatMap { v ->
                    val arr = (v as? JsonValue.Arr)?.value ?: return@flatMap emptyList()
                    val e = end ?: arr.size
                    arr.subList(start.coerceAtLeast(0), e.coerceAtMost(arr.size))
                }
            }
            else -> {
                val idx = inner.toIntOrNull()
                if (idx != null) {
                    cur.flatMap { v ->
                        val arr = (v as? JsonValue.Arr)?.value ?: return@flatMap emptyList()
                        val i = if (idx < 0) arr.size + idx else idx
                        if (i in arr.indices) listOf(arr[i]) else emptyList()
                    }
                } else {
                    // maybe quoted key without quotes? treat as key
                    cur.mapNotNull { v -> (v as? JsonValue.Obj)?.value?.get(inner) }
                }
            }
        }
    }

    private fun evalFilter(cond: String, elem: JsonValue): Boolean {
        // supports @.field == value  and @.field != value and @.field > n etc. and existence @.field
        val m = Regex("""@\.(.+?)\s*(==|!=|>=|<=|>|<)\s*(.+)""").find(cond)
        if (m != null) {
            val field = m.groupValues[1].trim()
            val op = m.groupValues[2]
            val rhsRaw = m.groupValues[3].trim()
            val lhs = (elem as? JsonValue.Obj)?.value?.get(field)
            val rhs = parseLiteral(rhsRaw)
            return cmp(lhs, op, rhs)
        }
        // existence
        if (cond.startsWith("@.")) {
            val field = cond.substring(2).trim()
            return (elem as? JsonValue.Obj)?.value?.containsKey(field) == true
        }
        return false
    }

    private fun parseLiteral(raw: String): JsonValue = when {
        raw.startsWith("'") || raw.startsWith("\"") -> JsonValue.Str(raw.trim('\'', '"'))
        raw == "true" -> JsonValue.Bool(true)
        raw == "false" -> JsonValue.Bool(false)
        raw == "null" -> JsonValue.Null
        else -> raw.toDoubleOrNull()?.let { JsonValue.Num(it) } ?: JsonValue.Str(raw)
    }

    private fun cmp(lhs: JsonValue?, op: String, rhs: JsonValue): Boolean {
        if (lhs == null) return op == "!=" 
        return when (op) {
            "==" -> lhs == rhs || (lhs is JsonValue.Num && rhs is JsonValue.Num && lhs.value == rhs.value) || (lhs is JsonValue.Str && rhs is JsonValue.Str && lhs.value == rhs.value)
            "!=" -> !(lhs == rhs)
            ">", ">=", "<", "<=" -> {
                val a = (lhs as? JsonValue.Num)?.value; val b = (rhs as? JsonValue.Num)?.value
                if (a == null || b == null) false
                else when (op) { ">" -> a > b; ">=" -> a >= b; "<" -> a < b; else -> a <= b }
            }
            else -> false
        }
    }
}
