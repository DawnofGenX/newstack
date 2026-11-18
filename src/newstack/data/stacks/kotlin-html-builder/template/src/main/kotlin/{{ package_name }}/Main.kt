package {{ package_name }}

fun main() {
    val page = html {
        head { }
        body {
            h1 { text("Hello") }
            p { text("It's <safe> & sound") }
            div {
                attr("class", "box")
                text("content")
            }
            a {
                attr("href", "https://example.com/?q=1&x=2")
                text("link")
            }
            br()
            img().attr("src", "x.png").attr("alt", "pic")
        }
    }
    println(page)
}
