package {{ package_name }}

import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test

class JsonTest {
    @Test
    fun rendersDeterministic() {
        val json = obj {
            str("name", "Ada")
            num("age", 30)
            bool("active", true)
            arr("tags") { str("kotlin"); str("json") }
            obj("address") { str("city", "NY"); nullValue("zip") }
        }
        assertEquals(
            """{"name":"Ada","age":30,"active":true,"tags":["kotlin","json"],"address":{"city":"NY","zip":null}}""",
            json.render()
        )
    }

    @Test
    fun escapesStrings() {
        val json = obj { str("msg", "a\"b\\c") }
        assertEquals("""{"msg":"a\"b\\c"}""", json.render())
    }

    @Test
    fun emptyContainers() {
        assertEquals("{}", obj {}.render())
        assertEquals("[]", arr {}.render())
    }
}
