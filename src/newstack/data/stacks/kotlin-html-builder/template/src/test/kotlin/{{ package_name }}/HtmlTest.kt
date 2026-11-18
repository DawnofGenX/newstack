package {{ package_name }}

import org.junit.jupiter.api.Test
import org.junit.jupiter.api.Assertions.*

class HtmlTest {
    @Test
    fun escapesText() {
        val t = p { text("<b>x & y</b>") }
        assertEquals("<p>&lt;b&gt;x &amp; y&lt;/b&gt;</p>", t.toString())
    }

    @Test
    fun escapesAttributes() {
        val t = div { attr("title", "a\"b") }
        assertEquals("<div title=\"a&quot;b\"></div>", t.toString())
    }

    @Test
    fun voidTags() {
        assertEquals("<br>", br().toString())
        assertEquals("<img src=\"x.png\" alt=\"pic\">", img().attr("src","x.png").attr("alt","pic").toString())
    }

    @Test
    fun nested() {
        val t = div { }
        t.child(p { text("hi") })
        assertEquals("<div><p>hi</p></div>", t.toString())
    }
}
