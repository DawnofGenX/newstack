package {{ package_name }}

fun escapeHtml(s: String): String =
    s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\"", "&quot;")

private val VOID_TAGS = setOf("br", "hr", "img", "input", "meta", "link")

class Tag(val name: String) {
    private val attrs = linkedMapOf<String, String>()
    private val children = mutableListOf<String>()

    fun attr(name: String, value: String): Tag {
        attrs[name] = value
        return this
    }

    fun text(s: String): Tag {
        children.add(escapeHtml(s))
        return this
    }

    fun raw(s: String): Tag {
        children.add(s)
        return this
    }

    fun child(tag: Tag): Tag {
        children.add(tag.toString())
        return this
    }

    override fun toString(): String {
        val attrStr = attrs.entries.joinToString(" ") { (k, v) ->
            "$k=\"${escapeHtml(v)}\""
        }
        val open = if (attrStr.isEmpty()) "<$name>" else "<$name $attrStr>"
        return if (name in VOID_TAGS) {
            open
        } else {
            "$open${children.joinToString("")}</$name>"
        }
    }
}

fun tag(name: String, block: Tag.() -> Unit = {}): Tag {
    val t = Tag(name)
    t.block()
    return t
}

fun html(block: Tag.() -> Unit): String = tag("html", block).toString()
fun head(block: Tag.() -> Unit): Tag = tag("head", block)
fun body(block: Tag.() -> Unit): Tag = tag("body", block)
fun div(block: Tag.() -> Unit): Tag = tag("div", block)
fun p(block: Tag.() -> Unit): Tag = tag("p", block)
fun span(block: Tag.() -> Unit): Tag = tag("span", block)
fun h1(block: Tag.() -> Unit): Tag = tag("h1", block)
fun a(block: Tag.() -> Unit): Tag = tag("a", block)
fun br(): Tag = tag("br")
fun img(): Tag = tag("img")
fun input(): Tag = tag("input")
