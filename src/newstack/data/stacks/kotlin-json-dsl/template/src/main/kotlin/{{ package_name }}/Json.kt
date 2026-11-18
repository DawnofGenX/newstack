package {{ package_name }}

import kotlin.collections.linkedMapOf

sealed interface Json {
    fun render(): String
}

object JsonNull : Json {
    override fun render(): String = "null"
}

data class JsonBool(val value: Boolean) : Json {
    override fun render(): String = if (value) "true" else "false"
}

data class JsonNumber(val value: Number) : Json {
    override fun render(): String = value.toString()
}

data class JsonString(val value: String) : Json {
    override fun render(): String = "\"" + escape(value) + "\""
}

data class JsonArray(val items: List<Json>) : Json {
    override fun render(): String = "[" + items.joinToString(",") { it.render() } + "]"
}

data class JsonObject(val fields: LinkedHashMap<String, Json>) : Json {
    override fun render(): String = "{" + fields.entries.joinToString(",") { "\"" + escape(it.key) + "\":" + it.value.render() } + "}"
}

private fun escape(value: String): String =
    buildString {
        for (c in value) {
            when (c) {
                '"' -> append("\\\"")
                '\\' -> append("\\\\")
                '\n' -> append("\\n")
                '\r' -> append("\\r")
                '\t' -> append("\\t")
                else -> {
                    if (c.code < 0x20) append("\\u%04x".format(c.code)) else append(c)
                }
            }
        }
    }

class JsonArrayBuilder {
    private val items = mutableListOf<Json>()
    fun add(value: Json) { items += value }
    fun str(value: String) = add(JsonString(value))
    fun num(value: Number) = add(JsonNumber(value))
    fun bool(value: Boolean) = add(JsonBool(value))
    fun nullValue() = add(JsonNull)
    fun obj(init: JsonObjectBuilder.() -> Unit) = add(JsonObjectBuilder().apply(init).build())
    fun arr(init: JsonArrayBuilder.() -> Unit) = add(JsonArrayBuilder().apply(init).build())
    fun build(): JsonArray = JsonArray(ArrayList(items))
}

class JsonObjectBuilder {
    private val fields = linkedMapOf<String, Json>()
    fun add(key: String, value: Json) { fields[key] = value }
    fun str(key: String, value: String) = add(key, JsonString(value))
    fun num(key: String, value: Number) = add(key, JsonNumber(value))
    fun bool(key: String, value: Boolean) = add(key, JsonBool(value))
    fun nullValue(key: String) = add(key, JsonNull)
    fun obj(key: String, init: JsonObjectBuilder.() -> Unit) = add(key, JsonObjectBuilder().apply(init).build())
    fun arr(key: String, init: JsonArrayBuilder.() -> Unit) = add(key, JsonArrayBuilder().apply(init).build())
    fun build(): JsonObject = JsonObject(LinkedHashMap(fields))
}

fun obj(init: JsonObjectBuilder.() -> Unit): JsonObject = JsonObjectBuilder().apply(init).build()
fun arr(init: JsonArrayBuilder.() -> Unit): JsonArray = JsonArrayBuilder().apply(init).build()
