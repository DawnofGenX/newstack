package {{ package_name }}

import java.nio.charset.StandardCharsets

/** Pure counting logic, with no I/O so it can be tested directly. */
object TextStat {

    /** Counts the raw bytes, and decodes them as UTF-8 to count lines and words. */
    fun count(data: ByteArray): Counts {
        val text = String(data, StandardCharsets.UTF_8)
        var lines = 0L
        var words = 0L
        var inWord = false
        for (current in text) {
            if (current == '\n') {
                lines++
            }
            if (current.isWhitespace()) {
                inWord = false
            } else if (!inWord) {
                inWord = true
                words++
            }
        }
        return Counts(lines, words, data.size.toLong())
    }

    /** Convenience overload for tests and callers that already hold text. */
    fun count(text: String): Counts = count(text.toByteArray(StandardCharsets.UTF_8))
}
