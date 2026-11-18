package {{ package_name }}

fun main() {
    val json = obj {
        str("name", "Ada")
        num("age", 30)
        bool("active", true)
        arr("tags") { str("kotlin"); str("json") }
        obj("address") { str("city", "NY"); nullValue("zip") }
    }
    println(json.render())
}
