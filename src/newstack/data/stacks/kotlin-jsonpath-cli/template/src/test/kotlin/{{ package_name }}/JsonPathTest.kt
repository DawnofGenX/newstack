package {{ package_name }}

import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test

class JsonPathTest {
    private val doc = """{"store":{"book":[{"category":"reference","author":"Nigel Rees","title":"Sayings of the Century","price":8.95},{"category":"fiction","author":"Evelyn Waugh","title":"Sword of Honour","price":12.99},{"category":"fiction","author":"Herman Melville","title":"Moby Dick","isbn":"0486229592","price":8.99}],"bicycle":{"color":"red","price":19.95}},"expensive":10}"""

    @Test
    fun parsesNumberAndString() {
        val v = Json.parse("""{"a":1,"b":"x"}""")
        assertEquals(JsonValue.Num(1.0), (v as JsonValue.Obj).value["a"])
        assertEquals(JsonValue.Str("x"), (v as JsonValue.Obj).value["b"])
    }

    @Test
    fun childAccess() {
        val root = Json.parse(doc)
        assertEquals(listOf(JsonValue.Str("red")), JsonPath.evaluate("$.store.bicycle.color", root))
    }

    @Test
    fun wildcardArray() {
        val root = Json.parse(doc)
        val res = JsonPath.evaluate("$.store.book[*].author", root)
        assertEquals(3, res.size)
        assertEquals(JsonValue.Str("Nigel Rees"), res[0])
        assertEquals(JsonValue.Str("Evelyn Waugh"), res[1])
        assertEquals(JsonValue.Str("Herman Melville"), res[2])
    }

    @Test
    fun arrayIndex() {
        val root = Json.parse(doc)
        assertEquals(listOf(JsonValue.Str("Evelyn Waugh")), JsonPath.evaluate("$.store.book[1].author", root))
    }

    @Test
    fun recursiveDescent() {
        val root = Json.parse(doc)
        val res = JsonPath.evaluate("$..price", root)
        assertEquals(4, res.size)
    }

    @Test
    fun filter() {
        val root = Json.parse(doc)
        val res = JsonPath.evaluate("$.store.book[?(@.price < 10)].title", root)
        assertEquals(2, res.size)
    }

    @Test
    fun rootReturnsSelf() {
        val root = Json.parse("42")
        assertEquals(listOf(JsonValue.Num(42.0)), JsonPath.evaluate("$", root))
    }

    @Test
    fun runInjectsIO() {
        val out = mutableListOf<String>()
        val err = mutableListOf<String>()
        val code = run(listOf("$.a"), { """{"a":7}""" }, { out.add(it) }, { err.add(it) })
        assertEquals(0, code)
        assertEquals(listOf("7"), out)
    }
}
